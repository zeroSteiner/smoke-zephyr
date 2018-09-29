:mod:`job` --- Asynchronous job manager
=======================================

.. module:: smoke_zephyr.job
   :synopsis: Asynchronous job manager

The :py:class:`.JobManager` provides a way to schedule jobs and run tasks
asynchronously from within python on the local system. In this case jobs are
callback functions defined by the user.

.. warning::
   The timing and scheduling functions within this module are not designed to be
   precise to the second.

Functions
---------

.. autofunction:: smoke_zephyr.job.normalize_job_id

Classes
-------

.. autoclass:: smoke_zephyr.job.JobManager
   :members:
   :special-members: __init__
   :undoc-members:

.. autoclass:: smoke_zephyr.job.JobRequestDelete
   :members:
   :special-members: __init__
   :undoc-members:
