**********
🏃‍ ️Usage
**********

This section describes how to use the PDS DOI Service.

The service is composed of command line tools (``pds-doi-cmd``, ``pds-doi-init``),
as well as a web API (``pds-doi-api``) which provides a REST interface to the DOI
service.

A DOI Service GUI is also available for interfacing with the web API from a browser,
however, it is provided as a separate application with its own github repository.
For more information on installing and running the PDS DOI UI, consult its `Readme`_.

At last, for operators who would need to process to bulk updates of the metadata
(e.g.  change all license information to X, in a CSV), an example **notebook for bulk updates** is provided.
It is self described and is meant to be adaptable for different cases.
See https://github.com/NASA-PDS/doi-service/blob/main/src/pds_doi_service/notebooks/Bulk%20Record%20Update.ipynb


Overview
========

A DOI (Digital Object Identifier) is a handle which is used to permanently identify
a digital object, typically a dataset or document. Once assigned, a DOI is
typically used to cite the digital object, especially in scientific papers.

In the context of PDS, publishing a new DOI follows this workflow:

    - ``Reserve``: Before a dataset is published in PDS, a DOI is reserved so the
      researchers working with the digital resource may cite it at early stage.
    - ``Update``: The metadata associated to an existing DOI is elaborated and validated,
      but without submission to the DOI provider (`DataCite`_).
    - ``Review``: Once all metadata has been properly associated to the DOI, the
      requester submits the DOI record for review to the PDS Engineering node.
    - ``Release``: After the PDS Engineering node determines that the DOI record is
      filled out properly, the DOI and its metadata are officially registered at
      `DataCite`_ and made available for public discovery. If there any issues with
      the reviewed record, PDS Engineering node may move the record back to a hidden
      status until correction by the original submitter. Corrections may be made
      via the ``Update`` action. Once updated, the record can be re-released to
      move it back to findable status.

The Update, Review and Release steps may be repeated multiple times to iterate on
the metadata associated to the DOI. However, a Reserve should only ever occur once.

The metadata managed with DOIs is meant to be preserved and traceable, as it is
used to permanently cite a digital resource. For this reason, all transactions,
creations, and updates with the PDS DOI Service are registered in a local database.
This database is used to track submissions-in-progress and help ensure the proper
workflow (``Reserve`` → ``Update`` → ``Review`` → ``Release``) is enforced.

Currently, the service provides a set command line tools for use by PDS Engineering
Node operators to interact directly with the local PDS DOI Service installation and its
transaction database. A web API is also available to facilitate management of DOIs
by other PDS discipline nodes (for example, when used with the DOI Service GUI).

Command Line Application Descriptions
=====================================

pds-doi-cmd
-----------

``pds-doi-cmd`` is the primary command line interface for interacting with the
PDS DOI Service. After installing the service and activating its virtual
environment, the ``pds-doi-cmd`` application may be accessed directly from the
command prompt::

    $ pds-doi-cmd --help

The application provides a number of subcommands for specific requests, which
loosely map to the workflow actions defined above. A subcommand must be specified
as the first argument to ``pds-doi-cmd``, after which, additional arguments may
be provided to configure the behavior of said subcommand. All subcommands provide
a ``--help`` flag to obtain a description of the available arguments::

    $ pds-doi-cmd reserve --help

Descriptions of the various subcommands and their usages are provided below.
For a full description of all available subcommand and their arguments, consult
the `api`_ section.

pds-doi-cmd reserve
^^^^^^^^^^^^^^^^^^^

The `reserve` subcommand allows a new DOI to be reserved by the DOI provider.
Once reserved, the assigned DOI may be used for citation purposes while metadata
is still being associated with the DOI record.

In DataCite parlance, a reserved DOI is initially kept in the "draft" state,
meaning the DOI is reserved, but not publicly findable. A draft DOI may also be
deleted using DataCite's REST API so the identifier may be returned to the pool
of reservable DOI's for PDS.

Input to the reserve subcommand is either a PDS4 XML label, or a spreadsheet in
CSV or Excel (.xls or .xlsx) format containing rows for each object to reserve a
DOI for. PDS4 labels are expected to conform to the PDS4 schema and not have a
DOI already assigned within them. Spreadsheets are expected to define several
mandatory columns and provide a header row with the name of each column (in any order).

An example CSV-format spreadsheet for a reserve request is provided below::

    title,publication_date,product_type_specific,author_last_name,author_first_name,related_resource
    Laboratory Shocked Feldspars Collection,2020-03-11,PDS4 Refereed Collection,Johnson,J. R.,urn:nasa:pds:lab_shocked_feldspars::1.0

Where the following are mandatory columns:
    * ``title`` : The title of the object to reserve a DOI for. Should not match any existing titles with DOI's assigned.
    * ``publication_date`` : The date of the object's publication in `YYYY-MM-DD` format.
    * ``product_type_specific`` : The type of the object. Should be one of `PDS4 Refereed Collection`, `PDS4 Refereed Document`, or `PDS4 Refereed Data Bundle` (note that `PDS3` may be used in lieu of `PDS4` if working with PDS3 objects)
    * ``author_last_name`` : Last name of the author of the object.
    * ``author_first_name`` : First name of the author of the object.
    * ``related_resource`` : The PDS4 LIDVID identifier associated with the object. If working with a PDS3 object, the PDS3 Site ID may be used instead.

Additionally, the following optional columns may also be provided:
    * ``doi`` : An existing DOI already assigned to the object. Should only be provided when using spreadsheets as input for an `update` or `release` action.
    * ``description`` : Free text description of the object.
    * ``site_url`` : URL to the landing page to be associated with the DOI.
    * ``node_id`` : A PDS node identifier to associate with the DOI metadata. Should be one of `atm`, `geo`, `img`, `naif`, `ppi`, `rs`, `rms`, or `sbn`.

If the reserve request is successful, the `reserve` subcommand returns a DataCite
format JSON label containing the reserved DOI records. This label may be saved
to disk and modified to include any additional metadata needed before release.
An updated JSON label may then be provided to the `update` or `release` actions, as
the workflow dictates.

pds-doi-cmd update
^^^^^^^^^^^^^^^^^^

The `update` subcommand allows the metadata associated with a reserved (or released)
record to be updated locally within the PDS DOI Service prior to submission to
DataCite. All updates made with the `update` action remain local to the installation
of the PDS DOI Service until released to DataCite, so an update request will not
change the findable status of an existing DOI record within DataCite.

Input to the `update` subcommand may be either a PDS4 label or spreadsheet (described
in the `reserve` section above), or a DataCite format JSON label. A DataCirte label
may be obtained as the output from a previous action or querired for via the `list`
action, described later in this document. Regardless of the format, the input must
define an existing DOI value for each provided record. These DOI values must also
already exist within the transaction database for the PDS DOI Service installation
(i.e. they were part of a previous reserve request made by the same installation of
the service).

If the update request is successful, the `update` subcommand returns a DataCite
format JSON label representing the updated state of each record. This label may
be saved off and reused with the `release` command to push the updates to DataCite.

pds-doi-cmd release
^^^^^^^^^^^^^^^^^^^

The `release` subcommand encompasses both the ``Review`` and ``Release`` steps
of the DOI workflow described above. It should be used when a reserved DOI
record is completed with all required metadata (via the `update` action).

According to DataCite's documentation, the following fields must be provided
before a release:

    * ``DOI`` : The DOI assigned by the reserve request
    * ``creators`` : The list of authors associated of the record
    * ``title`` : Title of the record
    * ``publisher`` : The publisher of the record
    * ``publicationYear`` : Year of record publication
    * ``resourceTypeGeneral`` : The type of record (dataset, document, etc.)

Note that all of these fields are set for you by the PDS DOI Service based on
values parsed from the input to a reserve request, however, they should not
typically not be removed or modified by update requests.

Whether the `release` action performs a release to the ``Review`` stage (for
internal review and approval by the PDS Engineering node) or directly to DataCite
as a findable record, is controlled by means of the ``--no-review`` argument to
the `release` subcommand.

To release a record to the ``Review`` stage::

    $ pds-doi-cmd release --input <your input file>

To release a record directly to DataCite::

    $ pds-doi-cmd release --no-review --input <your input file>

In DataCite parlance, released DOI records are moved into the "findable" state,
meaning they can be searched for on doi.org. A DOI moved to the findable state
may no longer be deleted (aka returned to the pool of our available DOI's), but
may still be updated or moved back into a hidden state. Note that moving a record
back to the hidden state currently **cannot** be performed via the PDS DOI Service.

The output of the `release` command is a DataCite format JSON label containing the
state of the record after release to review or DataCite.

pds-doi-cmd list
^^^^^^^^^^^^^^^^

The `list` subcommand is used primarily to query the local transaction database
for the current state of DOI record submission requests. User's may provide
one or more filters to subset query results to specific DOI's, PDS identifiers,
workflow status, or a start/end date range of last update.

A particularly useful use-case is using the `list` action to obtain the set of
DOI records in ``Review`` state which are awaiting approval by PDS Engineering
node prior to release to DataCite::

    $ pds-doi-cmd list --status review

Or checking the submission status for a particular LIDVID or Dataset ID::

    $ pds-doi-cmd list --ids urn:nasa:pds:lab_shocked_feldspars::1.0

Certain filter options, such as ``--ids``, ``--doi``, allow one or more Unix-style
wildcards (``*``) to be provided within each argument to pattern match against.
A useful case is obtaining all records associated to a LID with multiple VIDs::

    $ pds-doi-cmd list --ids urn:nasa:pds:lab_shocked_feldspars::*

By default, the results of a `list` query are returned as JSON-formatted database
records, reflecting the state of the DOI record within the transaction database.
However, the `list` subcommand may also be instructed to return matching records
as a DataCite format JSON label via the ``--format`` argument::

    $ pds-doi-cmd list --doi 10.12345/abcdef --format label

This can be very useful for obtaining a single label file containing multiple
records to be updated in tandem. The modified label may then be provided as the
input to the `update` or `release` subcommands.

pds-doi-cmd check
^^^^^^^^^^^^^^^^^

In older versions of the PDS DOI Service, the `check` subcommand was used to check
the state of DOI records that had been released, but left in a "pending" state by
the DOI provider. Since the transition to DataCite as the backend DOI provider,
the `check` action is no longer necessary and has been deprecated. It should no
longer be used.

Future versions of the PDS DOI Service may repurpose the `check` subcommand to be
useful within the context of DataCite submissions.


pds-doi-init
------------

The ``pds-doi-init`` command line application is used to synchronize the local
transaction database with the status of DOI records pulled directly from DataCite.
A DataCite format JSON label containing records may also be used in-lieu of a
direct pull from DataCite.

This script is useful in instances where a transaction database must be rebuilt
from scratch on a fresh installation of the service, or when an update to the
service invalidates an existing transaction database (due to table schema changes
and the like).

The script may also be used to pull entries from DataCite for DOI prefixes other
than the one assigned to PDS. This can be helpful for keeping in sync with other
PDS nodes that may have submitted DOI records with their own prefix.

Running ``pds-doi-init`` requires that the appropriate DataCite credentials and
endpoint URL are defined in the INI config. See the `installation`_ section for
more details.

A full description of the ``pds-doi-init`` application and its arguments may be
found in the `api`_ section.

pds-doi-api
-----------

The ``pds-doi-api`` script is the main interface for launching the REST API used
to interact with the core PDS DOI Service library. The script launches the API
within a `waitress`_ application server.

The host IP address and port the API binds to at launch are configured by the INI
config. See the `installation`_ section for more details on configuring the INI.

``pds-doi-api`` takes no arguments, however, it is typical to launch the API using
``screen`` or ``nohup`` to ensure the process remains after an operator has launched
it and logged out of the host system::

    $ nohup pds-doi-api > nohup.out &

You can explore the API documentation and test it using its built-in Swagger UI.
To access the test UI, navigate to http://localhost:8080/PDS_APIs/pds_doi_api/0.2/ui/
using a web-browser on the same machine that is running the API service (or a machine
with an SSH tunnel to the host machine). Note that this assumes the host and port
configured in the INI are set to ``localhost`` and ``8080``, respectively.

..  note::

    In order to access the built-in Swagger UI, there must **not** be any value
    set for the ``OTHER.api_valid_referrers`` section of the INI config. To
    ensure the value is not set, add the following the user configuration file
    described in the Configuration section above::

        [OTHER]
        api_valid_referrers =

A copy of the Swagger API definition, with available endpoints and URL query
parameters, for the ``pds-doi-api`` application is available within the `api`_ section.


Bulk Updates with Jupyter
=========================
Bulk updates of DOI records are most easily accomplished using Python Jupyter notebooks. There is an `example notebook <https://github.com/NASA-PDS/doi-service/blob/main/src/pds_doi_service/notebooks/Bulk%20Record%20Update.ipynb>`_ in the repo and a `tutorial for using the notebook <https://drive.google.com/file/d/13BecbQt1aUugct9830vpbnIIoMg_yXa2/view?usp=sharing>`_ posted on our internal Google Workspace Shared Drive.


.. _api: ../api/index.html
.. _installation: ../installation/index.html
.. _Readme: https://github.com/NASA-PDS/doi-ui#readme
.. _DataCite: https://datacite.org
.. _waitress: https://docs.pylonsproject.org/projects/waitress/en/latest/
