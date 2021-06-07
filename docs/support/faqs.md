# Frequently Asked Questions

This page includes FAQs for the PDS DOI Service. If you require additional support, please contact the [PDS Operator](mailto:pds-operator@jpl.nasa.gov) for assistance.

<!-- Use https://ecotrust-canada.github.io/markdown-toc/ to re-generate the TOC when new FAQs are added -->
- [How do I know whether I should reserve or release a DOI?](#how-do-i-know-whether-i-should-reserve-or-release-a-doi-)
- [How can I specify multiple authors in the DOI reserve spreadsheet?](#how-can-i-specify-multiple-authors-in-the-doi-reserve-spreadsheet-)
- [The DOI reserve spreadsheet seems very terse, can I provide more information?](#the-doi-reserve-spreadsheet-seems-very-terse--can-i-provide-more-information-)
- [What PDS4 products should we be assigning DOIs to?](#what-pds4-products-should-we-be-assigning-dois-to-)
- [What does it mean to have data registered?](#what-does-it-mean-to-have-data-registered-)
- [How do I register my PDS4 product with Engineering Node?](#how-do-i-register-my-pds4-product-with-engineering-node-)
- [How do I get a DOIs for PDS3 data sets and documents?](#how-do-i-get-a-dois-for-pds3-data-sets-and-documents-)

### How do I know whether I should reserve or release a DOI?

The short answer:
* If the data is not yet publicly available -> Reserve
* If the data is publicly available -> Release

The longer answer:
* To "reserve" a DOI, is to get a DOI from our DOI Provider associated with a data set for a future release. This is the ideal start for getting DOIs so you can get the DOI, and then add it to the PDS4 label metadata prior to release.
* To "release" a DOI is to make the `https://doi.org/<my_doi>` URL live. This requires that the data is registered at EN, available online, and the landing pages are live (automated by EN Registry).

### How can I specify multiple authors in the DOI reserve spreadsheet?

You can just put 1 author in the spreadsheet for now. The only part of that spreadsheet that really matters is the **LIDVID**. That is what ties to the DOI to the product. You will have a chance to update the DOI metadata with as many authors as you'd like at the "Release DOI" step.

### The DOI reserve spreadsheet seems very terse, can I provide more information?

The "Reserve DOI" step is really just a placeholder to request a DOI from our DOI Provider. The only information that is really critical at this step is the LIDVID. Everything else will be updated when you submit a request to "release" the DOI using the PDS4 label.

### What PDS4 products should we be assigning DOIs to?

Per the PDS DOI Policy, bundles are the "default" product to receive a DOI, but it is up to the Discipline Node if you would like DOIs for collections or documents.

### What does it mean to have data registered?

In order for the DOI Landing Pages to be generated, the products must be registered with PDS Engineering Node.

### How do I register my PDS4 product with Engineering Node?

Contact the [PDS Operator](mailto:pds-operator@jpl.nasa.gov) with the URL(s) to the applicable PDS4 product(s) you would like registered.

### How do I get a DOIs for PDS3 data sets and documents?

The PDS has gone through the exercise with each Discipline Node to mint DOIs for most PDS3 Data Sets. If we missed one or there is a new version available, please complete the following:

Send an email with the DS.CAT for all applicable PDS3 Data Sets to [PDS Operator](mailto:pds-operator@jpl.nasa.gov) and [Ron Joyner](mailto:ronald.joyner@jpl.nasa.gov) with subject `Release DOI for PDS3 Data Set: some identifying info`. Be sure to indicate whether the data set is new to the system, the DS.cat been updated, and if it has already been registered at PDS Engineering Node.
