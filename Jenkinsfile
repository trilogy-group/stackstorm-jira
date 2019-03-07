pipeline{
    environment {
        DOCKER_WKSPCE = '/opt/st2-docker'
        PACK_NAME='jira'
    }
    parameters {
        string(name: 'HOSTNAME', defaultValue: 'stackstorm.aureacentral.com', description: 'Enter vm ip address')
        string(name: 'USERNAME', defaultValue: 'ubuntuadmin', description: 'Enter stackstorm server user')
        string(name: 'SSH_KEY', defaultValue: "DEV_STACKSTORM_SSH-KEY", description: 'Enter stackstorm server ssh key')
        string(name: 'PACK_INSTALL_DIR', defaultValue: '/opt/stackstorm/packs', description: 'Enter stackstorm pack installation directory')
        string(name: 'AGENT_LABEL', defaultValue: 'firstrain-deploy', description: 'enter agent label to run this pipeline on.')

    }
    agent { label "${params.AGENT_LABEL}" }
    stages {
        stage('Test Host'){
            parallel{
                stage('SSH Host') {
                    steps {
                        sshagent (credentials: ["${params.SSH_KEY}"]) {
                            sh "ssh -o StrictHostKeyChecking=no -l ${params.USERNAME}  ${params.HOSTNAME} uname -a"
                        }
                    }
                }
            }
        }
        stage("Update/Install"){
             steps{
                    sshagent (credentials: ["${params.SSH_KEY}"]) {
                        sh 'printenv'
                        sh """
                            ssh -o StrictHostKeyChecking=no -l ${params.USERNAME}  ${params.HOSTNAME} 'rm -rf /tmp/${PACK_NAME};'
                            chmod -R 0777 ${WORKSPACE}
                            scp -o StrictHostKeyChecking=no -r ${WORKSPACE} ${params.USERNAME}@${params.HOSTNAME}:/tmp/ ;
                            """                       
                        sh """
                            ssh -o StrictHostKeyChecking=no -l ${params.USERNAME} ${params.HOSTNAME} '
                                cd ${DOCKER_WKSPCE};export STACKSTORM_CONTAINER_ID=\$(docker-compose ps -q stackstorm);
                                docker exec \${STACKSTORM_CONTAINER_ID} /bin/bash -c "rm -rf /tmp/${PACK_NAME}";
                                docker cp /tmp/${PACK_NAME} \${STACKSTORM_CONTAINER_ID}:/tmp/${PACK_NAME}/;
                                docker exec \${STACKSTORM_CONTAINER_ID} /bin/bash -c "ls -al /tmp/${PACK_NAME}; st2 pack install file:///tmp/${PACK_NAME} ; exit \$?";

                                #Cleanup
                                docker exec \${STACKSTORM_CONTAINER_ID} /bin/bash -c "rm -rf /tmp/${PACK_NAME}; exit \$?";
                                rm -rf /tmp/${PACK_NAME};

                            '
                            """

                    }
            }
        }
        stage('Validate'){
            steps {
                    sshagent (credentials: ["${params.SSH_KEY}"]) {
                        sh """
                        ssh -o StrictHostKeyChecking=no -l ${params.USERNAME}  ${params.HOSTNAME} '
                            cd ${DOCKER_WKSPCE};export STACKSTORM_CONTAINER_ID=\$(docker-compose ps -q stackstorm);
                            docker exec \${STACKSTORM_CONTAINER_ID} /bin/sh -c "st2 pack list;"
                        '
                        """
                    }
                }
        }

    }
    post { 
        success { 
            echo "${PACK_NAME} installed successfully!!!"
        }
        failure { 
            echo "${PACK_NAME} failed to install!!!"
        }
    }
}
