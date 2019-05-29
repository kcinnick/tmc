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

My current thinking is that if I just repeatedly scrape the recent posts page (https://teslamotorsclub.com/tmc/recent-posts/), that will provide the sufficient data to inform every other view (i.e. search by thread/poster/sentiment/keyword/etc.) in a database format.

Open questions:

- how to handle deleted/edited posts?
- How do we handle poll parsing? Do we even want to handle poll parsing?

TODO
----
- My thoughts on handling deleted posts currently are twofold: step one, setting up a database that records *only* a post's ID and if it had been deleted at last check.  This would not require changing the existing database, which I prefer as a solution because that database is constantly being written to.  Might need to be expanded in the future if I decide to tackle edited posts, which carry their own questions (do they show up in recent posts, etc.)

- Need to add method to ID posts that got skipped in the scraping process for whatever reason - current thinking is to do a left outer join against all currently possible post ID values and collect from there, while noting those values for future reference.

- Write a method for outputting last weeks/arbitrary date range's data to CSV format for data dumps.

- In consideration of things like sentiment analysis and overall data quality, need to come up with a way to handle posts that contain quotes of other posts. Quotes are easy to ID, so the only thing to decide is how exactly to handle this - maybe a "in reply to" column in the database?

- Write a method to plot # of comments for a time range, then narrow that to sentiment posts w/i time range, etc.

- Start uploading database dump when historical load is completed.

- Write tests that asserts random post has all the attrs we look for - to avoid any troubles coming up from using the fixture files.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
