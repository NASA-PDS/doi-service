/*
 * Copyright © 2022, California Institute of Technology ("Caltech").
 * U.S. Government sponsorship acknowledged.
 *
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * • Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 * • Redistributions must reproduce the above copyright notice, this list of
 * conditions and the following disclaimer in the documentation and/or other
 * materials provided with the distribution.
 * • Neither the name of Caltech nor its operating division, the Jet Propulsion
 * Laboratory, nor the names of its contributors may be used to endorse or
 * promote products derived from this software without specific prior written
 * permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

// Declarative Pipeline
// ====================
//
// This is a Jenkins pipline (of the declarative sort) for continuous deployment of the DOI service.
// For more information on pipelines, see: https://www.jenkins.io/doc/book/pipeline/syntax/

pipeline {

    // We want this to run exclusively on pds-expo.jpl.nasa.gov
    agent { node('pds-expo') }

    environment {
        // Pipeline-Specific Environtment
        // ------------------------------
        //
        // How long to wait (in seconds) before killing containers:
        shutdown_timeout = "30"

        // Basic composition command:
        compose = "docker-compose --file ${env.WORKSPACE}/jenkins-compose.yaml"

        // Network morphology
        PDS_DOI_PUBLISHED_PORT = "3176"
        PDS_DOI_TLS_PORT = "3177"
        CERT_CN = "pds-expo.jpl.nasa.gov"
        PROXY_REDIRECT = "http://pds-doi-api:8080/ https://pds-dev.jpl.nasa.gov/doi/"
    }

    options {
        // See the docs but these should be pretty obvious:
        skipStagesAfterUnstable()
        disableConcurrentBuilds()
    }

    stages {
        stage('🧱 Build') {
            // "Build" by making the config file for the Jenkins Composition.
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'datacite-dev', passwordVariable: 'p', usernameVariable: 'u')
                ]) {
                    sh "rm --force ${env.WORKSPACE}/doi_service.env"
                    sh "sed -e s=secret=$p=g -e s=username=$u=g ${env.WORKSPACE}/doi_service.env.in > ${env.WORKSPACE}/doi_service.env"
                }
            }
        }
        stage('🩺 Test') {
            // Upstream repo has already done tests thanks to CI, GitHub Actions, and Roundup. However,
            // we include the stage for reporting purposes (all pipelines should have a test stage).
            steps {
                echo 'No-op test step: ✓'
            }
        }
        stage('🚀 Deploy') {
            // Deployment is where the action happens: stop everything, then start 'em back up'.
            //
            // N.B.: `||:` is Bourne shell shorthand for "ignore errors".
            steps {
                sh "$compose down --remove-orphans --timeout ${shutdown_timeout} --volumes ||:"
                sh "$compose up --detach --quiet-pull --timeout ${shutdown_timeout}"
            }
            // 🔮 TODO: Include a `post {…}` block to do post-deployment test queries?
        }
    }
}
