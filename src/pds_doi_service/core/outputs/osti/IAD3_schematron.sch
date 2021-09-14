<?xml version="1.0" encoding="UTF-8"?>

<!-- PDS4 Schematron for Name Space Id:pds  Version:1.13.0.0 - Wed Sep 25 08:36:23 PDT 2019 -->
<!-- Generated from the PDS4 Information Model Version 1.13.0.0 - System Build 10a -->
<!-- *** This PDS4 schematron file is an operational deliverable. *** -->
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron">

    <sch:pattern>
        <sch:title>OSTI input document schema for 'release' action.</sch:title>

        <!--                                            -->
        <!-- not sure this rule is valid for both reserve & activate conditions ? -->
        <!--                                            -->
        <sch:rule context="id">
            <sch:let name="id_len" value="string-length(.)"/>

            <sch:assert test="$id_len = 0 or $id_len = 5 or $id_len = 7">
                if value is populated, the value in 'id' field must be exactly 7 characters long.  Length of value is: <sch:value-of select="$id_len"/>
            </sch:assert>
        </sch:rule>

        <sch:rule context="publication_date">
            <sch:assert test="text()">
                If exist, publication_date field may not be empty.
            </sch:assert>
        </sch:rule>

        <sch:rule context="product_type">
            <sch:let name="product_type_value" value="text()"/>

            <sch:assert test="text()">
                If exist, product_type field may not be empty.
            </sch:assert>
            <sch:assert test="$product_type_value = 'Bundle'
                              or $product_type_value = 'Collection'
                              or $product_type_value = 'Dataset'
                              or $product_type_value = 'Text'">
                If exist, product_type field should be either 'Bundle' or 'Collection' or 'Dataset'.
            </sch:assert>
        </sch:rule>

        <sch:rule context="product_type_specific">
            <sch:assert test="text()">
                If exist, product_type_specific field may not be empty.
            </sch:assert>
        </sch:rule>

        <sch:rule context="authors/author/first_name">
            <sch:assert test="string-length(normalize-space(.)) &gt;= 1">
                If exist, authors field containing 'first_name' must not be empty.
            </sch:assert>
        </sch:rule>
        <sch:rule context="authors/author/last_name">
            <sch:assert test="string-length(normalize-space(.)) &gt;= 1">
                If exist, authors field containing 'last_name' must not be empty.
            </sch:assert>
        </sch:rule>

        <sch:rule context="related_identifiers/related_identifier/identifier_value">
            <sch:assert test="string-length(normalize-space(.)) &gt;= 1">
                If exist, related_identifiers/related_identifier field containing 'identifier_value' must not be empty.
            </sch:assert>
        </sch:rule>
    </sch:pattern>
</sch:schema>
