# Cloudify Docker Plugin

This plugin provides the following functionality:

  * Installation, configuration and uninstallation of Docker on a machine
    [ could be the manager as well but better to have it on a different node ]
  * Representation of Docker modules [Image, Container] as Cloudify nodes
  * Building Docker Images
  * Run Docker container given the built images that you have
  * Retrieve host details
  * Retrieve all images on the system
  * Retrieve all containers on the system
  * Handle container volume mapping to the docker host for use inside the container

## Examples

See the [examples](examples) directory.
