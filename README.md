# ElectionSystem
Python project using Flask and SQLAlchemy libraries. Services are running in Docker containers on Docker Swarm infrastructure.

## Build the images
Build the images using .dockerfiles, and set their tags:
- authentication
- authenticationdbmigration
- damon
- admin
- electiondbmigration
- official

## Create cluster
##### Install Docker Machine
- install [docker-machine](https://github.com/docker/machine/releases/) and add it to the PATH

##### Create nodes
`docker-machine.exe create <node_name> --virtualbox-no-vtx-check`

##### Initialize cluster
You can connect to a node using `docker-machine ssh <node_name>`\
The node which executes this command, will become cluster manager: `docker swarm init --advertise-addr <ip_address_of_this_node>`\
You can check nodes ip addresses using `docker-machine ls`\
When you execute the above command, you will see a command, which you can execute on other nodes in order to become cluster workers\
You can see all nodes in the cluster using `docker node ls`\
You can see all the services running on the cluster using `docker service ls`

## Deploy application on a cluster
##### Create private repository
Images we want to deploy, we have to first push to our private repository
We will create a repository image, and run it on cluster as a service
- Add into Docker Engine: `"insecure-registries": ["<manager_ip_address>:5000"]`
- Add insecure registry to the swarm.
  1. `sudo su`
  2. `cd /var/lib/boot2docker`
  3. `vi profile`
  4. Add `--insecure-registry <manager_ip_address:5000>` inside `EXTRA_ARGS`
  5. Save and exit
  6. Restart manager `docker-machine restart manager`
- Run repository service (*on manager*) : `docker service create --name registry --replicas 1 --publish 5000:5000 registry:2`

##### Push images to the repository
*Commands are executed outside manager node*
1. Change tags of our **previously created** images into <manager_ip_addresss>:5000/<previous_image_tag>
  - `docker tag authentication <manager_ip_address>:5000/authentication`
  - `docker tag daemon <manager_ip_address>:5000/daemon`
  - etc
2. Push the images to the repository
  - `docker push <manager_ip_address>:5000/authentication`
  - `docker push <manager_ip_address>:5000/daemon`
  - etc

##### Pull the images from the repository
*Commands are executed inside manager node*
1. Pull the **prevoiusly pushed images from the repository**
  - `docker pull <manager_ip_address>:5000/authentication`
  - `docker pull <manager_ip_address>:5000/daemon`
  - etc
2. Change tags of our pulled images back to their original tags, because they refer to each other as that in the stack.yaml file
  - `docker tag <manager_ip_address>:5000/authentication authentication`
  - `docker tag <manager_ip_address>:5000/daemon daemon`
  - etc

##### Deploy the application on a cluster
*Copy the stack.yaml file to someplace on host machine, accessable to the linux vm*
1. Copy the stack.yaml to the linux: `/Path/to/stack.yaml stack.yaml`
2. Deploy the images: `docker stack deploy --compose-file stack.yaml election_stack`
