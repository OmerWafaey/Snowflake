docker run --rm -i --name Snowflake --entrypoint sh snowflake-test -c "ansible-playbook -i /ansible/inventory.ini /ansible/deploy_chromadb.yml"
