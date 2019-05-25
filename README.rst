===
tmc
===


Tesla Motor Club forum scraper.


* Free software: MIT license
* Documentation: https://tmc.readthedocs.io.

With the increased activity on the forums related to recent $TSLA occurrences (repairs being backed up, funding concerns at the company, etc.) I'm resuming active development on this module. :-)

Features
--------

* Scrape user info
* Scrape posts by user, thread, or post ID
* Retrieve sentiment for posts
* Search threads & posts

My current thinking is that if I just repeatedly scrape the recent posts page (https://teslamotorsclub.com/tmc/recent-posts/), that will provide the sufficient data to inform every other view (i.e. search by thread/poster/sentiment/keyword/etc.) in a database format.

Open questions:

- how to handle deleted/edited posts?
- database layer to use? leaning towards MySQL

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
