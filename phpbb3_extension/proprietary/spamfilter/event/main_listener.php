<?php

namespace proprietary\spamfilter\event;

/**
 * @ignore
 */
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Forum_spam_filter\SpamClassificationClient;
use Forum_spam_filter\MaybeSpam;
use Forum_spam_filter\SpamOrHam;

/**
 * spam filter Event listener.
 */
class main_listener implements EventSubscriberInterface
{
    public static function getSubscribedEvents()
    {
        return [
            'core.submit_post_end' => 'handle_submit',
            'core.user_setup' => 'load_language_on_setup',
        ];
    }

    /* @var \phpbb\language\language */
    protected $language;

    /* @var \phpbb\db\driver\driver_interface */
    protected $db;

    /* @var \phpbb\log\log_interface */
    protected $log;

    /* @var \phpbb\notification\manager */
    protected $notification_manager;

    /* @var SpamClassificationClient */
    private $grpc_client;

    /**
     * Constructor
     *
     * @param \phpbb\language\language	$language	Language object
     */
    public function __construct(
        \phpbb\language\language $language,
        \phpbb\db\driver\driver_interface $db,
        \phpbb\log\log_interface $log,
        ContainerInterface $container
    ) {
        $this->language = $language;
        $this->db = $db;
        $this->log = $log;
        $this->notification_manager = $container->get('notification_manager');
        $this->grpc_client = new SpamClassificationClient('forum-spam-filter:60066', [ // TODO: Make this configurable
            'credentials' => \Grpc\ChannelCredentials::createInsecure(),
        ]);
    }

    public function handle_submit($event)
    {
        $data = $event['data'];
        $post_text = $data['message'];
        $poster_id = (int) $data['poster_id'];
        if ($this->is_user_newly_registered($poster_id)
            && $this->is_in_moderation_queue((int) $data['post_id'])
            && $this->is_spam($post_text)) {
            $this->disapprove_post($data);
        }
    }

    private function is_spam(string $text): bool
    {
        $request = new MaybeSpam();
        $request->setText($text);
        list($response, $status) = $this->grpc_client->Classify($request)->wait();
        if ($status->code !== \Grpc\STATUS_OK) {
            echo 'Error: ' . $status->details . PHP_EOL;
            return false;
        } else {
            return $response->getProbability() > 0.8; // TODO: Make this configurable
        }
    }

    private function is_in_moderation_queue(int $post_id): bool
    {
        $sql = 'SELECT post_id '
               . 'FROM ' . POSTS_TABLE . ' '
               . 'WHERE post_id = ' . $post_id . ' AND post_visibility = ' . ITEM_UNAPPROVED;
        $result = $this->db->sql_query($sql);
        $row = $this->db->sql_fetchrow($result);
        $this->db->sql_freeresult($result);

        return !empty($row);
    }

    protected function disapprove_post($data)
    {
        $time = time();
        $reason = $this->language->lang('SPAMFILTER_DISAPPROVAL_REASON');

        // Retrieve all columns of this post
        $result = $this->db->sql_query(
            "SELECT " . POSTS_TABLE . ".*, " . FORUMS_TABLE . ".forum_name as forum_name"
            . " FROM " . POSTS_TABLE
            . " JOIN " . FORUMS_TABLE . " ON " . POSTS_TABLE . ".forum_id = " . FORUMS_TABLE . ".forum_id"
            . " WHERE post_id = " . (int) $data['post_id']
        );
        $post_row = $this->db->sql_fetchrow($result);
        $this->db->sql_freeresult($result);

        // Retrieve all columns of this topic
        $result = $this->db->sql_query('SELECT * FROM ' . TOPICS_TABLE . ' WHERE topic_id = ' . (int) $data['topic_id']);
        $topic_row = $this->db->sql_fetchrow($result);
        $this->db->sql_freeresult($result);

        // Reconstruct the payload for the notification
        $notification_data = array_merge($post_row, array(
            'user_id' => $data['poster_id'],
            'topic_title' => $topic_row['topic_title'],
            'post_subject' => $post_row['post_subject'],
            'post_id' => $data['post_id'],
            'topic_id' => $data['topic_id'],
            'poster_id' => $post_row['poster_id'],
            'forum_id' => $data['forum_id'],
            'disapprove_reason' => $reason,
            'post_subject' => $post_row['post_subject'],
            'post_time' => $post_row['post_time'],
            'post_username' => $post_row['post_username'],
            'message' => $post_row['post_text'],
            'notification_time' => $time,
        ));

        // Delete the notification to mods to approve the post
        $this->notification_manager->delete_notifications('notification.type.post_in_queue', $notification_data);

        // Soft delete the post
        $this->db->sql_query('UPDATE ' . POSTS_TABLE
                             . ' SET post_visibility = ' . ITEM_DELETED
                             . ', post_delete_user = ' . ANONYMOUS
                             . ', post_delete_time = ' . $time
                             . ', post_delete_reason = "' . $this->db->sql_escape($reason) . '"'
                             . ' WHERE post_id = ' . (int) $data['post_id']);

        if ((int) $topic_row['topic_first_post_id'] == (int) $data['post_id']) {
            // When this post is actually a new topic, then soft delete the topic, too.
            $this->db->sql_query('UPDATE ' . TOPICS_TABLE
                                 . ' SET topic_visibility = ' . ITEM_DELETED
                                 . ', topic_delete_reason = "' . $this->db->sql_escape($reason) . '"'
                                 . ', topic_delete_user = ' . ANONYMOUS
                                 . ', topic_delete_time = ' . $time
                                 . ' WHERE topic_id = ' . (int) $data['topic_id']);
            // Delete the notification to mods to approve the topic
            $this->notification_manager->delete_notifications('notification.type.topic_in_queue', $notification_data);
        } elseif ((int) $topic_row['topic_last_post_id'] == (int) $data['post_id']) {
            // When this post is the last post of a topic, then update the last post of the topic.
            $result = $this->db->sql_query('SELECT MAX(post_id) as last_post_id, COUNT(post_id) as visible_posts'
                                           . ' FROM ' . POSTS_TABLE
                                           . ' WHERE topic_id = ' . (int) $data['topic_id']
                                           . ' AND post_visibility = ' . ITEM_APPROVED);
            $new_topic_stats = $this->db->sql_fetchrow($result);
            $this->db->sql_freeresult($result);
            if ($new_last_post) {
                $this->db->sql_query('UPDATE ' . TOPICS_TABLE
                                     . ' SET topic_last_post_id = ' . (int) $row['post_id']
                                     . ' WHERE topic_id = ' . (int) $data['topic_id']);
                // If there are no visible posts left in this topic, then soft delete the topic.
                if ((int) $new_last_post['visible_posts'] == 0) {
                    $this->db->sql_query('UPDATE ' . TOPICS_TABLE
                                        . ' SET topic_visibility = ' . ITEM_DELETED
                                        . ', topic_delete_reason = "' . $this->db->sql_escape($reason) . '"'
                                        . ', topic_delete_user = ' . ANONYMOUS
                                        . ', topic_delete_time = ' . $time
                                        . ' WHERE topic_id = ' . (int) $data['topic_id']);
                }
            }
        }

        // Log the disapproval in the moderator log
        $this->log->add('mod', ANONYMOUS, '127.0.0.1', 'SPAMFILTER_LOG_DISAPPROVAL', false, array(
            'forum_id' => $data['forum_id'],
            'topic_id' => $data['topic_id'],
            'post_id' => $data['post_id'],
            $reason
        ));

        // Notify user about the disapproval
        if ((int) $data['poster_id'] != ANONYMOUS) {
            $this->notification_manager->add_notifications('notification.type.disapprove_post', $notification_data);
        }
    }

    /**
     * Check if the user is a member of the newly registered group.
     */
    protected function is_user_newly_registered(int $user_id): bool
    {
        $sql = 'SELECT ' . USER_GROUP_TABLE . '.group_id
                FROM ' . USER_GROUP_TABLE . '
                JOIN ' . GROUPS_TABLE . ' ON ' . USER_GROUP_TABLE . '.group_id = ' . GROUPS_TABLE . '.group_id
                WHERE ' . USER_GROUP_TABLE . '.user_id = ' . $user_id . '
                AND ' . GROUPS_TABLE . '.group_name = "NEWLY_REGISTERED"';
        $result = $this->db->sql_query($sql);
        $row = $this->db->sql_fetchrow($result);
        $this->db->sql_freeresult($result);

        return !empty($row);
    }


    /**
     * Load common language files during user setup
     *
     * @param \phpbb\event\data	$event	Event object
     */
    public function load_language_on_setup($event)
    {
        $lang_set_ext = $event['lang_set_ext'];
        $lang_set_ext[] = [
          'ext_name' => 'proprietary/spamfilter',
          'lang_set' => 'common',
        ];
        $event['lang_set_ext'] = $lang_set_ext;
    }
}
