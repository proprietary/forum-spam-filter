import unittest
import os
import tempfile
from forum_spam_filter.clean_data.spam_assassin import parse_email, load_spam_assassin


class TestSimpleEmailParsing(unittest.TestCase):
    SAMPLE_EMAIL = """
From fork-admin@xent.com  Wed Aug 28 10:50:29 2002
Return-Path: <fork-admin@xent.com>
Delivered-To: yyyy@localhost.netnoteinc.com
Received: from localhost (localhost [127.0.0.1])
  by phobos.labs.netnoteinc.com (Postfix) with ESMTP id CBC6A44156
  for <jm@localhost>; Wed, 28 Aug 2002 05:50:08 -0400 (EDT)
Received: from phobos [127.0.0.1]
  by localhost with IMAP (fetchmail-5.9.0)
  for jm@localhost (single-drop); Wed, 28 Aug 2002 10:50:08 +0100 (IST)
Received: from xent.com ([64.161.22.236]) by dogma.slashnull.org
    (8.11.6/8.11.6) with ESMTP id g7RLFhZ26129 for <jm@jmason.org>;
    Tue, 27 Aug 2002 22:15:43 +0100
Received: from lair.xent.com (localhost [127.0.0.1]) by xent.com (Postfix)
    with ESMTP id AE7E42940D8; Tue, 27 Aug 2002 14:13:09 -0700 (PDT)
Delivered-To: fork@example.com
Received: from mail.evergo.net (unknown [206.191.151.2]) by xent.com
    (Postfix) with SMTP id 94B3729409A for <fork@xent.com>; Tue,
    27 Aug 2002 14:12:25 -0700 (PDT)
Received: (qmail 2729 invoked from network); 27 Aug 2002 21:14:27 -0000
Received: from dsl.206.191.151.102.evergo.net (HELO JMHALL)
    (206.191.151.102) by mail.evergo.net with SMTP; 27 Aug 2002 21:14:27 -0000
Reply-To: <johnhall@evergo.net>
From: "John Hall" <johnhall@evergo.net>
To: <fork@example.com>
Subject: RE: The Curse of India's Socialism
Message-Id: <007001c24e0e$b4e9e010$0200a8c0@JMHALL>
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
X-Priority: 3 (Normal)
X-Msmail-Priority: Normal
X-Mailer: Microsoft Outlook, Build 10.0.2627
In-Reply-To: <1030396738.2767.162.camel@avalon>
X-Mimeole: Produced By Microsoft MimeOLE V6.00.2600.0000
Importance: Normal
Sender: fork-admin@xent.com
Errors-To: fork-admin@xent.com
X-Beenthere: fork@example.com
X-Mailman-Version: 2.0.11
Precedence: bulk
List-Help: <mailto:fork-request@xent.com?subject=help>
List-Post: <mailto:fork@example.com>
List-Subscribe: <http://xent.com/mailman/listinfo/fork>, <mailto:fork-request@xent.com?subject=subscribe>
List-Id: Friends of Rohit Khare <fork.xent.com>
List-Unsubscribe: <http://xent.com/mailman/listinfo/fork>,
    <mailto:fork-request@xent.com?subject=unsubscribe>
List-Archive: <http://xent.com/pipermail/fork/>
Date: Tue, 27 Aug 2002 14:14:18 -0700
X-Pyzor: Reported 0 times.
X-Spam-Status: No, hits=-7.1 required=7.0
  tests=IN_REP_TO,KNOWN_MAILING_LIST,QUOTED_EMAIL_TEXT,
        SPAM_PHRASE_00_01
  version=2.40-cvs
X-Spam-Level:


> From: fork-admin@xent.com [mailto:fork-admin@xent.com] On Behalf Of
James
> Rogers

> Subject: Re: The Curse of India's Socialism
>
> On Tue, 2002-08-20 at 15:01, Ian Andrew Bell wrote:

> > They
> > finished their routine with the a quadruple lutz -- laying off
> > hundreds of thousands of workers when it all came crashing down.
>
> So what?  Nobody is guaranteed employment.  Laying people off is not a
> crime nor is it immoral.  Companies don't exist to provide employment,
> nor should they.  The closest we have to such a thing in the US is a
> Government Job, and look at the quality THAT breeds.

And further, why focus on the fact they were laid off and not on the
fact they were hired in the first place?

BTW: I saw someone claim that aside from the efficiency of the market
there were also gains to society from irrational behavior.

If a society has business people that systematically overestimate their
chances, that is bad for the businessmen but on net a big gain for
society.  On the social level, the law of averages works to societies
benefit in a manner it can't for an individual.

A key reason, in this view, that the US wound up outperforming England
was that the English investors were too rational for their societies own
good.

(Except, of course, when US investors were bilking them to build canals
and railroads over here.  Thanks, guys.)

=====================

Applied to telecom: a lot of dark wire (glass) and innovation will
eventually be used for pennies on the dollar, the benefits to society
and the costs to the investors.
    """

    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(self.SAMPLE_EMAIL.encode())
            self.tmpfile = tmp.name

    def tearDown(self):
        os.unlink(self.tmpfile)

    def test_simple_email_parsing(self):
        with open(self.tmpfile, "rb") as f:
            body = parse_email(f)
        self.assertIn("railroads", body)


class TestLoadDataset(unittest.TestCase):
    def test_load_spam_assassin(self):
        df = load_spam_assassin()
        self.assertIsNotNone(df)


if __name__ == "__main__":
    unittest.main()
