parcel
------

Packaging tools for shanty services.

What?
=====

Services are docker containers deployed by shanty on a hosting appliance. Each service consists of the main parts:

 - A docker image
 - A service definition (.yml file used by docker)
 - Metadata, a name, description, dependencies and author information
 - Configuration, variable declarations to be used in the service defition.

A service is packaged as a tarball, minimal tarball contents would be:

.. code-block:: bash

    /
    - manifest.json
    - service.yml
    /.signatures/
    - manifest.json.sig
    - service.yml.sig
  
``manifest.json`` contains metadata about the service, ``service.yml``
contains the docker service definitions. Variable substitution is performed
on ``service.yml`` before it is deployed. Variables can be sourced from
``manifest.json`` or can include values from the hosting appliance settings.
an example ``manifest.json`` might look like:

.. code-block:: javascript

    {
      "name": "example",
      "author": "btimby@gmail.com",
      "version": "0.9.8",
      "image": "shantysocial/echo",
      "image_tag": "12934324",
      "service_definition": "service.yml",
      "variables": {
      },
      "settings": [
        "SHANTY_OAUTH_TOKEN"
      ],
      "options": {
        "OPTION_A_ENABLED": {
          "type": "boolean",
          "description": "Toggles option A",
          "default": true
        }
      },
      "files": [
        "foo_config.cfg"
      ]
    }

NOTE: The author email address is significant in that it defines the PGP key
used to sign and verify the parcel file.

Settings are pulled from the shanty appliance global configuration. Options
are obtained from the user at installation time. Options are private to the
service while settings are global.

The corresponding ``service.yml`` file might look like this:

.. code-block:: yaml

    version: "3"

    services:
      example:
        image: this_value_is_ignored_and_can_be_omitted
        environment:
          - ENV_VAR0_NAME=${SHANTY_OAUTH_TOKEN}
          - ENV_VAR1_NAME=${OPTION_A_ENABLED}
      configs:
        - source: foo_config
          target: /etc/foo_config/foo_config.cfg
          mode: 0444

    configs:
      foo_config:
        file: foo_config.cfg


How?
====

You must first write a ``manifest.json`` file and ``service.yml`` if the
``service.yml`` refers to any configuration files, the must be named in the
``manifest.json`` so that they are bundled. File names must be unique.

Once you have your manifest, you can package it by running ``shanty-parcel``

.. code-block:: bash

    $ shanty-parcel lint manifest.json
    $ shanty-parcel build --lint manifest.json

Which will first check for common errors, and then produce the parcel file
``example.pcl``.

Library
=======

This package can also be used as a library, for loading, verifying and
preparing pacels for deployment.

.. code-block:: python

    from pprint import pprint
    import docker
    import shanty_parcel


    p = shanty_parcel.load('example.pcl', verify=True)

    # You can also lazily check the signature.
    p.verify()

    # Print the contents.
    pprint(p.files)

    # Configure the service.
    config = {}
    for option in p.options:
        value = input(f"Please enter a value of type {option.type} for {option.name} [enter for default: {option.default}] ")
        config[option.name] = value

    print("Example needs the following settings:")
    for setting in p.settings:
        print(f" - {setting.name}")

    p.configure(config, settings)

    # Save the .yml and supporting files in given directory.
    p.write('/path/for/output/')

    # Deploy the service.
    docker.swarm.deploy('/path/for/output/example.yml')
