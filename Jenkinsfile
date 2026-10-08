// ---------------------------------------------------------------
// LabLend CI/CD pipeline
//   Checkout -> Build test image -> Unit tests (pytest) ->
//   Build Docker image -> Deploy with Docker Compose -> Smoke test
// The Jenkins agent only needs the Docker CLI: tests run inside
// the "test" stage of the project Dockerfile.
// ---------------------------------------------------------------
pipeline {
    agent any

    options {
        skipDefaultCheckout()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
        timeout(time: 20, unit: 'MINUTES')
    }

    environment {
        APP_IMAGE  = 'lablend-web'
        TEST_IMAGE = 'lablend-test'
        APP_URL    = 'http://host.docker.internal:5000'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        stage('Build Test Image') {
            steps {
                sh 'docker build --target test -t ${TEST_IMAGE}:${BUILD_NUMBER} .'
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    mkdir -p test-reports
                    docker rm -f lablend-test-${BUILD_NUMBER} >/dev/null 2>&1 || true
                    docker run --name lablend-test-${BUILD_NUMBER} ${TEST_IMAGE}:${BUILD_NUMBER} \
                        pytest -v --junitxml=/tmp/junit.xml
                '''
            }
            post {
                always {
                    sh '''
                        docker cp lablend-test-${BUILD_NUMBER}:/tmp/junit.xml test-reports/junit.xml || true
                        docker rm -f lablend-test-${BUILD_NUMBER} >/dev/null 2>&1 || true
                    '''
                    junit allowEmptyResults: true, testResults: 'test-reports/junit.xml'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build --target production -t ${APP_IMAGE}:${BUILD_NUMBER} -t ${APP_IMAGE}:latest .'
                sh 'docker images ${APP_IMAGE}'
            }
        }

        stage('Deploy (Docker Compose)') {
            steps {
                sh '''
                    export APP_VERSION=1.0.${BUILD_NUMBER}
                    docker compose up -d
                    docker compose ps
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    for i in $(seq 1 20); do
                        if curl -fs ${APP_URL}/health; then
                            echo ""
                            echo "LabLend is UP after deployment"
                            exit 0
                        fi
                        sleep 3
                    done
                    echo "LabLend did not become healthy"
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo "Build #${BUILD_NUMBER} deployed successfully: http://localhost:5000"
        }
        failure {
            echo "Build #${BUILD_NUMBER} failed - check the stage logs above."
        }
        always {
            sh 'docker image prune -f >/dev/null 2>&1 || true'
        }
    }
}
