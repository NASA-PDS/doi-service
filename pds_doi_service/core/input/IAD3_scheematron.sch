<?xml version="1.0" encoding="UTF-8"?>

<!-- IAD XML schema 
    History:
      - Versoon 1.0.0: 20200705; by Neal Ensor; modified extensively by R.Joyner
      - Version 1.1.0: 20201026; by R.Joyner; 
                         - added test for LIDVID required in <accession_number> and in <identifier_value> and in the legacy <report_numbers>
                         - added test to ensure compatibility between <product_type> and <accession_number> | <identifier_value> | and legacy <report_numbers>
-->

<!-- PDS4 Schematron for Name Space Id:pds  Version:1.13.0.0 - Wed Sep 25 08:36:23 PDT 2019 -->
<!-- Generated from the PDS4 Information Model Version 1.13.0.0 - System Build 10a -->
<!-- *** This PDS4 schematron file is an operational deliverable. queryBinding="xslt2" *** -->
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" >

    <!-- begin EDIT 20201015 -->
    <!-- added test for LIDVID required in <accession_number> and in <identifier_value> and in the legacy <report_numbers>  -->
    
    <sch:pattern>
        <sch:let name="urn_nasa" value="'urn:nasa:pds:'"/>
        <sch:let name="urn_pds3_dataset" value="'urn:nasa:pds:context_pds3:data_set:'"/>
        
        <sch:let name="pds3_dataset_test" value="not (records/record/product_type_specific = 'PDS3 Refereed Data Set')"/>
        
        <!--
            <sch:let name="lid_required_colons" value="4"/>
        -->
        <sch:let name="lidvid_required_colons" value="4"/>   <!-- minimum number of colons in PDS4 product -->
        
        <sch:rule context="site_url">
            <sch:let name="site_url_jpl" value="'https://pds.jpl.nasa.gov/ds-view/pds/view'"/>
            <sch:let name="site_url_pds" value="'https://pds.nasa.gov/ds-view/pds/view'"/>


            <!-- Test for site_url starts-with either: 'https://pds.jpl.nasa.gov/ds-view/pds/view' or 'https://pds.nasa.gov/ds-view/pds/view' -->
            <!-- Could make this test more specific based on: product_type_specific -->
            <!--
            <sch:assert test="(not (contains(., $site_url_jpl))) and (not (contains(., $site_url_pds)))">
                The value of the attribute 'site_url' must start with either: 'https://pds.jpl.nasa.gov/ds-view/pds/view' or 'https://pds.nasa.gov/ds-view/pds/view'.</sch:assert>
            -->
            <sch:assert test="(starts-with(., $site_url_jpl)) or (starts-with(., $site_url_pds))">
                The value of the attribute 'site_url' must start with either: 'https://pds.jpl.nasa.gov/ds-view/pds/view' or 'https://pds.nasa.gov/ds-view/pds/view'.</sch:assert>
            
        </sch:rule>
        
        <sch:rule context="record/related_identifiers/related_identifier/identifier_value">
            <sch:let name="identifier_lidvid_num_colons" value="string-length(.) - string-length(translate(., ':', ''))"/>
            
            <!--
            <sch:assert test="false()">
                <sch:value-of select="$pds3_dataset_test"/> - The value of '$pds3_dataset_test'</sch:assert>
            -->

            <!-- Test for '::' -->
            <!--    - only PDS4 Products contain '::' -->
            <!--    - PDS3 dataset do not -->    
            <sch:assert test="if ($pds3_dataset_test) then contains(.,'::') else true()">
                The value of the attribute 'related_identifier/identifier_value' must include a value that contains '::' followed by version id</sch:assert>
            
            <!-- Test for starts-with 'urn:nasa:pds:' -->                             
            <sch:assert test="if (.) then starts-with(., $urn_nasa) else true()">
                The value of the attribute 'related_identifier/identifier_value' must start with: <sch:value-of select="$urn_nasa"/></sch:assert>

            <!-- Test if PDS3 dataset starts-with 'urn:nasa:pds:context_pds3:data_set:' -->                             
            <sch:assert test="if (not ($pds3_dataset_test)) then starts-with(., $urn_pds3_dataset) else true()">
                For PDS3 DataSets, the value of the attribute 'related_identifier/identifier_value' must start with: <sch:value-of select="$urn_pds3_dataset"/></sch:assert>
            
            <!-- Test for minimum colons; ensure minimum # of colons present -->                             
            <sch:assert test="(not ($identifier_lidvid_num_colons &lt; $lidvid_required_colons))">
                The value of the attribute 'related_identifier/identifier_value' must contain a minimum number of '<sch:value-of select="$lidvid_required_colons"/> colons. 
                Found '<sch:value-of select="$identifier_lidvid_num_colons"/> colons.</sch:assert>
            
        </sch:rule>

        <sch:rule context="record/accession_number">
            <sch:let name="accession_lidvid_num_colons" value="string-length(.) - string-length(translate(., ':', ''))"/>
  
            <!-- Test for '::' -->
            <!--    - only PDS4 Products contain '::' -->
            <!--    - PDS3 dataset do not -->    
            <sch:assert test="if ($pds3_dataset_test) then contains(.,'::') else true()">
                The value of the attribute 'accession_number' must include a value that contains '::' followed by version id</sch:assert>
                         
            <!-- Test for contains 'urn:nasa:pds:' -->                             
            <sch:assert test="if (.) then starts-with(., $urn_nasa) else true()">
                The value of the attribute 'accession_number' must start with: <sch:value-of select="$urn_nasa"/></sch:assert>

            <!-- Test if PDS3 dataset starts-with 'urn:nasa:pds:context_pds3:data_set:' -->                             
            <sch:assert test="if (not ($pds3_dataset_test)) then starts-with(., $urn_pds3_dataset) else true()">
                For PDS3 DataSets, the value of the attribute 'accession_number' must start with: <sch:value-of select="$urn_pds3_dataset"/></sch:assert>
            
            <!-- Test for minimum colons; ensure minimum # of colons present -->                             
            <sch:assert test="(not ($accession_lidvid_num_colons &lt; $lidvid_required_colons))">
                The value of the attribute 'accession_number' must contain a minimum number of '<sch:value-of select="$lidvid_required_colons"/> colons. 
                Found '<sch:value-of select="$accession_lidvid_num_colons"/> colons.</sch:assert>
            
        </sch:rule>

        <sch:rule context="record/report_numbers"> 
            <sch:let name="report_lidvid_num_colons" value="string-length(.) - string-length(translate(., ':', ''))"/>

            <!-- Test for '::' -->
            <!--    - only PDS4 Products contain '::' -->
            <!--    - PDS3 dataset do not -->    
            <sch:assert test="if ($pds3_dataset_test) then contains(.,'::') else true()">
                The value of the attribute 'report_numbers' must include a value that contains '::' followed by version id</sch:assert>
            
             <!-- Test for contains 'urn:nasa:pds:' -->                             
            <sch:assert test="if (.) then starts-with(., $urn_nasa) else true()">
                The value of the attribute 'report_numbers' must start with: <sch:value-of select="$urn_nasa"/></sch:assert>

            <!-- Test if PDS3 dataset starts-with 'urn:nasa:pds:context_pds3:data_set:' -->                             
            <sch:assert test="if (not ($pds3_dataset_test)) then starts-with(., $urn_pds3_dataset) else true()">
                For PDS3 DataSets, the value of the attribute 'report_numbers' must start with: <sch:value-of select="$urn_pds3_dataset"/></sch:assert>
            
            <!-- Test for minimum colons; ensure minimum # of colons present -->                             
            <sch:assert test="(not ($report_lidvid_num_colons &lt; $lidvid_required_colons))">
                The value of the attribute 'report_numbers' must contain a minimum number of '<sch:value-of select="$lidvid_required_colons"/> colons. 
                Found '<sch:value-of select="$report_lidvid_num_colons"/> colons.</sch:assert>
            
        </sch:rule>
        
        
    </sch:pattern>
    
    <!-- end EDIT -->
    



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

        <sch:rule context="site_url">
            <sch:assert test="text()">
                If exist, site_url field may not be empty.
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

