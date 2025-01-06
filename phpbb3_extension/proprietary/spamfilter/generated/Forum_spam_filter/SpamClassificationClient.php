<?php

// GENERATED CODE -- DO NOT EDIT!

namespace Forum_spam_filter;

/**
 */
class SpamClassificationClient extends \Grpc\BaseStub
{
    /**
     * @param string $hostname hostname
     * @param array $opts channel options
     * @param \Grpc\Channel $channel (optional) re-use channel object
     */
    public function __construct($hostname, $opts, $channel = null)
    {
        parent::__construct($hostname, $opts, $channel);
    }

    /**
     * @param \Forum_spam_filter\MaybeSpam $argument input argument
     * @param array $metadata metadata
     * @param array $options call options
     * @return \Grpc\UnaryCall
     */
    public function Classify(
        \Forum_spam_filter\MaybeSpam $argument,
        $metadata = [],
        $options = []
    ) {
        return $this->_simpleRequest(
            '/forum_spam_filter.SpamClassification/Classify',
            $argument,
            ['\Forum_spam_filter\SpamOrHam', 'decode'],
            $metadata,
            $options
        );
    }

}
