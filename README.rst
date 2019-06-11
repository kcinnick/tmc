===
tmc
===


Tesla Motor Club forum scraper.


* Free software: MIT license
* Documentation: https://tmc.readthedocs.io.

With the increased activity on the forums related to recent $TSLA occurrences (repairs being backed up, funding concerns at the company, etc.) I'm resuming active development on this module. This is a work in progress and I'd greatly appreciate any suggestions or thoughts on it!

Features
--------

* Scrape user info
* Scrape posts by user, thread, or post ID
* Retrieve sentiment for posts
* Search threads & posts
* Scrape recent posts
* Upload scraped posts to a database
* Search database for any date range, post ID, username, etc.
* Export scraped posts to CSV 

My current thinking is that if I just repeatedly scrape the recent posts page (https://teslamotorsclub.com/tmc/recent-posts/), that will provide the sufficient data to inform every other view (i.e. search by thread/poster/sentiment/keyword/etc.) in a database format.  This strategy seems to be working so far.

Open questions:

- how to handle deleted/edited posts?
- How do we handle poll parsing? Do we even want to handle poll parsing? FWIW, I'm currently leaning towards no - both because it'd be a pain in the butt to keep updated and I'm not convinced there's much value in it.

TODO
----
- My thoughts on handling deleted posts currently are twofold: step one, setting up a database that records *only* a post's ID and if it had been deleted at last check.  This would not require changing the existing database, which I prefer as a solution because that database is constantly being written to.  Might need to be expanded in the future if I decide to tackle edited posts, which carry their own questions (do they show up in recent posts, etc.)  This has become more of a priority because deleted posts are always going to show as 'tbd' under the current logic because they can never be evaluated - just catching with try/excepts for now but more permanent solution is needed.

- Re-scrape old posts to get "in reply to" value/fix message value (ugh)

- Create some sort of automated daily DB dump solution.

Current Focus
------
- Re-scraping old posts to get "in reply to" value/fix message value (ugh)
- Adding "in reply to" logic to current scraping

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
