pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        DOCKERHUB_USERNAME = 'sagar07ai'
        IMAGE_NAME = 'image-details'
        TRIVY_IMAGE = 'aquasec/trivy:0.74.0@sha256:62b1e65e8869bc4b4c6aa4fa2b21595256c7c2f6018a9d9ad61caf87187c1969'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Inspect Repository') {
            steps {
                sh '''
                    set -eu
                    test -f image_details/Dockerfile
                    test -f image_details/Dockerfile.test
                    test -f image_details/requirements-dev.txt
                    test -d image_details/app
                    test -d image_details/tests
                    ls -la image_details
                '''
            }
        }

        stage('Docker Check') {
            steps {
                sh '''
                    docker --version
                    docker info --format '{{.ServerVersion}}'
                '''
            }
        }

        stage('Unit and API Tests') {
            steps {
                dir('image_details') {
                    sh '''
                        set -eu
                        mkdir -p test-results
                        rm -f test-results/pytest.xml

                        docker build --pull \
                          --file Dockerfile.test \
                          --tag ${IMAGE_NAME}-tests:${BUILD_NUMBER} \
                          .

                        test_container="${IMAGE_NAME}-tests-${BUILD_NUMBER}"
                        docker create \
                          --name "$test_container" \
                          ${IMAGE_NAME}-tests:${BUILD_NUMBER}

                        test_status=0
                        report_status=0
                        docker start --attach "$test_container" || test_status=$?
                        docker cp \
                          "$test_container:/workspace/test-results/pytest.xml" \
                          test-results/pytest.xml || report_status=$?
                        docker rm "$test_container"

                        if [ "$test_status" -ne 0 ]; then
                            exit "$test_status"
                        fi
                        exit "$report_status"
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                dir('image_details') {
                    sh '''
                        docker build --pull \
                          --tag ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${BUILD_NUMBER} \
                          --tag ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest \
                          .
                    '''
                }
            }
        }

        stage('Verify Docker Image') {
            steps {
                sh '''
                    docker image inspect \
                      ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${BUILD_NUMBER}
                '''
            }
        }

        stage('Trivy Security Gate') {
            steps {
                sh '''
                    set -eu
                    scan_archive="${WORKSPACE}/image-details-${BUILD_NUMBER}.tar"
                    scan_container="${IMAGE_NAME}-trivy-${BUILD_NUMBER}"

                    docker image save \
                      --output "$scan_archive" \
                      ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${BUILD_NUMBER}

                    docker pull ${TRIVY_IMAGE}
                    docker create \
                      --name "$scan_container" \
                      ${TRIVY_IMAGE} \
                      image \
                      --input /tmp/image.tar \
                      --severity CRITICAL \
                      --ignore-unfixed \
                      --exit-code 1 \
                      --no-progress

                    docker cp \
                      "$scan_archive" \
                      "$scan_container:/tmp/image.tar"

                    scan_status=0
                    docker start --attach "$scan_container" || scan_status=$?
                    docker rm "$scan_container"
                    rm -f "$scan_archive"

                    exit "$scan_status"
                '''
            }
        }

        stage('Docker Hub Login') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {
                    sh '''
                        echo "$DOCKER_PASSWORD" | \
                        docker login \
                          --username "$DOCKER_USER" \
                          --password-stdin
                    '''
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                sh '''
                    docker push \
                      ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${BUILD_NUMBER}

                    docker push \
                      ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest
                '''
            }
        }
    }

    post {
        always {
            junit(
                testResults: 'image_details/test-results/pytest.xml',
                allowEmptyResults: true
            )

            sh '''
                docker logout || true
                docker rm --force \
                  ${IMAGE_NAME}-tests-${BUILD_NUMBER} || true
                docker rm --force \
                  ${IMAGE_NAME}-trivy-${BUILD_NUMBER} || true
                rm -f \
                  "${WORKSPACE}/image-details-${BUILD_NUMBER}.tar"
                docker image rm \
                  ${IMAGE_NAME}-tests:${BUILD_NUMBER} || true
                docker image rm \
                  ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${BUILD_NUMBER} || true
                docker image rm \
                  ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest || true
            '''
        }

        success {
            echo 'CI pipeline completed successfully.'
        }

        failure {
            echo 'CI pipeline failed before an unsafe image could be pushed.'
        }
    }
}
