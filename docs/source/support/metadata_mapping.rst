.. _metadata_mapping:

PDS4 to DataCite Metadata Mapping
===================================

This page documents how the PDS DOI Service maps PDS4 XML label fields to
`DataCite Metadata Schema`_ fields, which default values are applied automatically,
and guidelines for curating the remaining fields.

For general metadata quality guidelines, see the
`DOI Metadata Guidelines <https://pds-engineering.jpl.nasa.gov/discipline-node-help/doi/#best-practices>`_
page on the PDS Engineering Node site.

.. contents:: On this page
   :local:
   :depth: 2

---

Parsed from PDS4 Label
-----------------------

The following DataCite fields are populated by parsing the submitted PDS4 XML label.
XPath expressions use the ``pds4:`` prefix bound to ``http://pds.nasa.gov/pds4/pds/v1``.

.. list-table::
   :header-rows: 1
   :widths: 28 32 40

   * - DataCite Field
     - PDS4 XPath
     - Notes
   * - ``titles[].title``
     - ``/*/pds4:Identification_Area/pds4:title``
     - Language set to ``en``. Should be descriptive enough to stand alone
       in an ADS search result. Should include product type, processing level,
       and version where applicable.
   * - ``descriptions[].description``
     - ``/*/pds4:Identification_Area/pds4:Citation_Information/pds4:description``
     - ``descriptionType`` set to ``Abstract``, language ``en``. Should be
       written as a standalone abstract suitable for non-PDS audiences. Expand
       all acronyms; avoid short-form citations unless the DOI is also included.
   * - ``publicationYear``
     - ``/*/pds4:Identification_Area/pds4:Modification_History/pds4:Modification_Detail/pds4:modification_date``
       (earliest date if multiple present), falling back to
       ``/*/pds4:Identification_Area/pds4:Citation_Information/pds4:publication_year``
     - Four-digit year extracted from the resolved date. For accumulating
       collections, should reflect the year the data was **first published**
       (recommended by ADS).
   * - ``identifiers[].identifier``
     - ``/*/pds4:Identification_Area/pds4:logical_identifier`` + ``::`` +
       ``/*/pds4:Identification_Area/pds4:version_id``
     - ``identifierType`` set to ``Site ID``. This is the LIDVID.
   * - ``types.resourceType`` / ``types.resourceTypeGeneral``
     - ``/*/pds4:Identification_Area/pds4:product_class``
     - See :ref:`product_type_mapping` below.
   * - ``creators[]``
     - ``/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_Author/pds4:Person/*``
       or ``pds4:Organization/*``
     - Structured ``List_Author`` elements take precedence over the legacy
       ``pds4:author_list`` free-text field. See :ref:`author_mapping`.
   * - ``contributors[]`` (Editor)
     - ``/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_Editor/pds4:Person/*``
       or ``pds4:Organization/*``
     - Structured ``List_Editor`` elements take precedence over the legacy
       ``pds4:editor_list`` free-text field. ``contributorType`` set to ``Editor``.
   * - ``contributors[]`` (other types)
     - ``/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_Contributor/pds4:Person/*``
       or ``pds4:Organization/*``
     - Appended to the contributors list alongside editors. ``contributorType``
       comes from the ``pds4:contributor_type`` element within the label.
   * - ``subjects[]``
     - Extracted from ``pds4:Context_Area`` fields — see :ref:`keywords_mapping`.
     - Auto-generated and may not follow UAT vocabulary; review and clean up.
   * - Existing ``doi``
     - ``/*/pds4:Identification_Area/pds4:Citation_Information/pds4:doi``
     - Only present if the label already has a DOI assigned. Do **not** set this
       manually to avoid overwriting existing DOIs.

.. _author_mapping:

Author / Creator Mapping
~~~~~~~~~~~~~~~~~~~~~~~~~

The service supports two mechanisms for specifying authors in PDS4 labels. The
structured ``List_Author`` class is preferred and, if present, supersedes the
legacy ``author_list`` free-text field.

**Structured (preferred) — ``List_Author``:**

Each ``<Person>`` or ``<Organization>`` element within
``/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_Author``
is parsed with the following field mappings:

.. list-table::
   :header-rows: 1
   :widths: 35 35 30

   * - PDS4 element
     - DataCite creator field
     - Notes
   * - ``pds4:given_name``
     - ``name`` (first part) / ``nameType: Personal``
     - Combined with ``family_name`` as ``"given last"``
   * - ``pds4:family_name``
     - ``name`` (second part) / ``nameType: Personal``
     -
   * - ``pds4:person_orcid``
     - ``nameIdentifiers[].nameIdentifier`` (scheme: ``ORCID``)
     -
   * - ``pds4:Affiliation/pds4:organization_name``
     - ``affiliation[].name``
     -
   * - ``pds4:organization_name`` (inside ``<Organization>``)
     - ``name`` / ``nameType: Organizational``
     -
   * - ``pds4:organization_rorid`` (inside ``<Organization>``)
     - ``nameIdentifiers[].nameIdentifier`` (scheme: ``ROR``)
     -
   * - ``pds4:contributor_type``
     - Used to classify the role (Author, Editor, Contributor)
     -

.. note::
   The Jinja template currently hardcodes ``"nameType": "Personal"`` for all
   editor/contributor entries in the DataCite output, regardless of whether the
   PDS4 label specifies an ``<Organization>``. Organizational editors are output
   correctly by name but will carry ``nameType: Personal`` until this is fixed.

**Legacy — ``author_list`` (free text):**

The ``/*/pds4:Identification_Area/pds4:Citation_Information/pds4:author_list``
field is a plain text string. The service uses heuristics to detect whether names
are separated by commas or semicolons, then parses each name into ``first_name``
/ ``last_name`` components. This method cannot carry ORCIDs, affiliations, or
name types — use the structured ``List_Author`` class whenever possible.

.. _keywords_mapping:

Keywords / Subjects Mapping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``subjects[]`` are auto-generated from several ``pds4:Context_Area`` fields using
an internal keyword tokenizer:

- ``/*/pds4:Context_Area/pds4:Investigation_Area/pds4:name``
- ``/*/pds4:Context_Area/pds4:Observing_System/pds4:Observing_System_Component/pds4:name``
- ``/*/pds4:Context_Area/pds4:Target_Identification/pds4:name``
- ``/*/pds4:Context_Area/pds4:Primary_Result_Summary/*``

Two global keywords — ``PDS`` and ``PDS4`` — are always included (configured
via ``OTHER.global_keyword_values`` in the INI). The auto-generated subjects
are **not** sourced from the Unified Astronomy Thesaurus (UAT). Curators should
review and replace or supplement them with UAT terms where possible. UAT keywords
can be found at https://astrothesaurus.org.

.. _product_type_mapping:

Product Type Mapping
~~~~~~~~~~~~~~~~~~~~~

The ``product_class`` element drives both ``resourceTypeGeneral`` and
``resourceType`` in DataCite:

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - PDS4 ``product_class``
     - DataCite ``resourceTypeGeneral``
     - DataCite ``resourceType``
   * - ``Product_Bundle``
     - ``Collection``
     - ``PDS4 Refereed Data Bundle``
   * - ``Product_Collection``
     - ``Collection``
     - ``PDS4 Refereed Data Collection``
   * - ``Product_Document``
     - ``Text``
     - ``PDS4 Refereed Document``
   * - Any other ``Product_*`` (e.g. ``Product_Observational``)
     - ``Dataset``
     - ``PDS4 Refereed Data {suffix}`` (e.g. ``PDS4 Refereed Data Observational``)

---

Auto-generated Fields
----------------------

The following fields are set automatically by the DOI Service and should **not**
be modified manually.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - DataCite Field
     - Value / Behavior
   * - ``doi``
     - Assigned by DataCite at reserve time. Do **not** set or change this value.
   * - ``url``
     - Auto-generated PDS landing page URL derived from the LIDVID and product
       type. Format varies by product type, e.g.
       ``https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?...``
   * - ``publisher``
     - Always ``NASA Planetary Data System`` (from ``OTHER.doi_publisher`` in
       the INI config).
   * - ``contributors[DataCurator]``
     - Always ``Planetary Data System: {Node} Node`` where ``{Node}`` is the
       long name of the PDS node supplied via the ``--node`` argument at
       reserve time (e.g., ``Geosciences``, ``Small Bodies``, ``Atmospheres``).
       Valid node IDs and their long names:

       - ``atm`` → Atmospheres
       - ``eng`` → Engineering
       - ``geo`` → Geosciences
       - ``img`` → Cartography and Imaging Sciences Discipline
       - ``naif`` → Navigational and Ancillary Information Facility
       - ``ppi`` → Planetary Plasma Interactions
       - ``rs`` → Radio Science
       - ``rms`` → Ring-Moon Systems
       - ``sbn`` → Small Bodies
   * - ``rightsList``
     - Always two entries:

       1. *U.S. Government Works* — ``"This is a work of the U.S. Government
          and is not subject to copyright protection in the United States.
          Foreign copyrights may apply."``
          URI: ``https://www.usa.gov/government-works``

       2. *CC0-1.0* — Creative Commons Zero v1.0 Universal.
          URI: ``http://creativecommons.org/publicdomain/zero/1.0/``
          Identifier scheme: ``SPDX``
   * - ``language``
     - Always ``en``.
   * - ``schemaVersion``
     - Always ``http://datacite.org/schema/kernel-4``.

---

Fields Requiring Manual Curation
----------------------------------

The following fields are either absent from typical PDS4 labels or require
human judgment to populate correctly. They can be added or updated via the
``update`` action using a DataCite JSON label as input.

``descriptions[]``
~~~~~~~~~~~~~~~~~~~

If the PDS4 label's ``Citation_Information/description`` is missing or
insufficient, provide an abstract-quality description. It should:

- Be suitable for a non-PDS audience (e.g., ADS users)
- Expand all acronyms
- Not include short-form citations (``Author, Year``) unless the full DOI
  is also provided as ``https://doi.org/<doi>``

``subjects[]`` (UAT keywords)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Auto-generated subjects come from the PDS4 context area and may not be
accurate or use controlled vocabulary. Replace or supplement with terms
from the `Unified Astronomy Thesaurus (UAT) <https://astrothesaurus.org>`_.

Example of well-formed UAT subjects::

    "subjects": [
      {
        "subject": "Kreutz Sungrazers",
        "subjectScheme": "UAT",
        "schemeUri": "https://astrothesaurus.org",
        "valueUri": "https://astrothesaurus.org/uat/890"
      }
    ]

``relatedIdentifiers[]``
~~~~~~~~~~~~~~~~~~~~~~~~~

Use this field to cite other data sets and publications that were
**essential to the creation** of this data set (not merely useful for
using it). Think of it like references in a journal article.

Use ``relationType: "Cites"`` for outgoing citations. Use
``relationType: "IsCitedBy"`` for papers that reference this data set.

Example::

    "relatedIdentifiers": [
      {
        "relatedIdentifier": "10.26007/6C3R-SD58",
        "relatedIdentifierType": "DOI",
        "relationType": "Cites"
      }
    ]

``dates[]`` (Available date)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``Available`` date (year + month) is used by ADS to generate usage
statistics over time. It must agree with ``publicationYear``.

.. note::
   The current DOI Service does not yet populate this field automatically.
   It must be added manually when curating the DOI metadata.

Example::

    "dates": [
      { "date": "2010-04-01", "dateType": "Available" }
    ]

``creators[].nameIdentifiers``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using the legacy ``author_list`` free-text field, no ORCIDs can be
captured. To add ORCIDs post-reserve, update the DataCite JSON label
directly, or switch the PDS4 label to use the structured ``List_Author``
class before reserving.

---

.. _DataCite Metadata Schema: https://schema.datacite.org/
