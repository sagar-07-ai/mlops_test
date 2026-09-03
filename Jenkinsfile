pipeline {
    agent any

    environment {
        DOCKERHUB_USERNAME = 'sagar07ai'
        IMAGE_NAME = 'image-details'
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
                    echo "===== Jenkins User ====="
                    whoami

                    echo "===== Jenkins Workspace ====="
                    pwd

                    echo "===== Repository ====="
                    ls -la

                    echo "===== Verification Service ====="
                    ls -la verification
                '''
            }
        }

        stage('Docker Check') {
            steps {
                sh '''
                    docker --version
                    docker ps
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                dir('image_details') {
                    sh '''
                        docker build \
                          -t ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${BUILD_NUMBER} \
                          -t ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest \
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
                          -u "$DOCKER_USER" \
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
            sh 'docker logout || true'
        }

        success {
            echo 'CI pipeline completed successfully.'
        }

        failure {
            echo 'CI pipeline failed.'
        }
    }
}
