import docker
import mock
import unittest

from uuid import uuid1

from cloudify.mocks import MockCloudifyContext

from docker_plugin.tasks import make_docker_client, build_image, delete_image, create_container, FROM_IMAGE, \
    start_container, stop_container, delete_container, create_network, delete_network, create_volume, delete_volume


class TestPlugin(unittest.TestCase):
    image_id = 'sha256:abc123'
    docker_client_name = 'docker.DockerClient'

    def setUp(self):
        super(TestPlugin, self).setUp()

    def test_should_make_docker_client_without_tls(self):
        settings = self.given_empty_tls_setting()

        client = make_docker_client(settings)

        self.then_client_is_connected(client)

    def test_should_build_existing_image_from_repository(self):
        client = self.given_mock_client()
        ctx = self.given_ctx_with_existing_docker_from_repository()

        with mock.patch(self.docker_client_name, client):
            build_image(ctx)

        self.then_image_is_built(ctx)

    def test_should_build_new_image_from_repository(self):
        client = self.given_mock_client_without_image()
        ctx = self.given_ctx_with_docker_from_repository()

        with mock.patch(self.docker_client_name, client):
            build_image(ctx)

        self.then_image_is_built(ctx)

    def test_should_remove_image(self):
        ctx = self.given_ctx_with_image()
        client = self.given_simple_client()

        with mock.patch(self.docker_client_name, client):
            delete_image(ctx)

        self.then_image_is_deleted(client)

    def test_should_not_remove_image_whit_keep_property(self):
        ctx = self.given_ctx_with_image_and_keep_property()
        client = self.given_simple_client()

        with mock.patch(self.docker_client_name, client):
            delete_image(ctx)

        self.then_image_is_not_deleted(client)

    def test_should_create_container(self):
        ctx = self.given_ctx_with_relationship()
        client = self.given_simple_client()

        with mock.patch(self.docker_client_name, client):
            create_container(ctx)

        self.then_container_is_created(client)

    def test_should_not_create_container_without_relation(self):
        ctx = self.given_ctx_with_image()
        client = self.given_mock_client()

        with mock.patch(self.docker_client_name, client):
            with self.assertRaises(RuntimeError):
                create_container(ctx)

    def test_should_start_container(self):
        ctx = self.given_ctx_with_container()
        client, container = self.given_mock_client_with_container()

        with mock.patch(self.docker_client_name, client):
            start_container(ctx)

        self.then_container_is_started(container)

    def test_should_stop_container(self):
        ctx = self.given_ctx_with_container()
        client, container = self.given_mock_client_with_container()

        with mock.patch(self.docker_client_name, client):
            stop_container(ctx)

        self.then_container_is_stopped(container)

    def test_should_delete_container(self):
        ctx = self.given_ctx_with_container()
        client, container = self.given_mock_client_with_container()

        with mock.patch(self.docker_client_name, client):
            delete_container(ctx)

        self.then_container_is_removed(container)

    def test_should_not_create_network_when_already_exists(self):
        ctx = self.given_ctx_with_network()
        client = self.given_simple_client()

        with mock.patch(self.docker_client_name, client):
            with self.assertRaises(RuntimeError):
                create_network(ctx)

    def test_should_create_network(self):
        ctx = self.given_ctx_with_network()
        client = self.given_client_without_network()

        with mock.patch(self.docker_client_name, client):
            create_network(ctx)

        self.then_network_is_created(client)

    def test_should_delete_network(self):
        ctx = self.given_ctx_with_network_id(external=False)
        client, network = self.given_client_with_network()

        with mock.patch(self.docker_client_name, client):
            delete_network(ctx)

        self.then_network_is_deleted(client, network)

    def test_should_not_delete_external_network(self):
        ctx = self.given_ctx_with_network_id(external=True)
        client, network = self.given_client_with_network()

        with mock.patch(self.docker_client_name, client):
            delete_network(ctx)

        self.then_network_is_not_deleted(client, network)

    def test_should_create_volume(self):
        ctx = self.given_ctx_with_volume(mountpoint=None)
        client = self.given_simple_client()

        with mock.patch(self.docker_client_name, client):
            create_volume(ctx)

        self.then_volume_is_created(client)

    def test_not_should_create_volume_with_mountpoint(self):
        ctx = self.given_ctx_with_volume(mountpoint='test')
        client = self.given_simple_client()

        with mock.patch(self.docker_client_name, client):
            create_volume(ctx)

        self.then_volume_is_not_created(client)

    def test_should_delete_volume(self):
        ctx = self.given_ctx_with_existining_volume(created=True)
        client, volume = self.given_client_with_volume()

        with mock.patch(self.docker_client_name, client):
            delete_volume(ctx)

        self.then_volume_is_deleted(client, volume)

    def test_should_not_delete_existing_volume(self):
        ctx = self.given_ctx_with_existining_volume(created=False)
        client, volume = self.given_client_with_volume()

        with mock.patch(self.docker_client_name, client):
            delete_volume(ctx)

        self.then_volume_is_not_deleted(client, volume)

    @staticmethod
    def given_empty_tls_setting():
        return {}

    def given_mock_client(self):
        def get(repository):
            self.assertEqual('existing:latest', repository)
            image = mock.Mock()
            image.id = self.image_id
            return image

        mock_images = mock.Mock()
        mock_images.images.get.side_effect = get
        client = mock.MagicMock(return_value=mock_images)
        return client

    def given_mock_client_without_image(self):
        def get(repository):
            self.assertEqual('notexisting:latest', repository)
            raise docker.errors.ImageNotFound(mock.Mock())

        def pull(repository, tag):
            self.assertEqual('notexisting', repository)
            self.assertEqual('latest', tag)
            image = mock.Mock()
            image.id = self.image_id
            return image

        mock_images = mock.Mock()
        mock_images.images.get.side_effect = get
        mock_images.images.pull.side_effect = pull
        client = mock.MagicMock(return_value=mock_images)
        return client

    def given_simple_client(self):
        mock_images = mock.Mock()
        client = mock.MagicMock(return_value=mock_images)
        return client

    def given_client_without_network(self):
        def get(network_name):
            self.assertEqual('test_network', network_name)
            raise docker.errors.NotFound(mock.Mock())

        networks = mock.Mock()
        networks.networks.get.side_effect = get
        client = mock.MagicMock(return_value=networks)
        return client

    def given_client_with_network(self):
        network = mock.MagicMock()

        def get(network_name):
            self.assertEqual('test_network', network_name)
            return network

        networks = mock.Mock()
        networks.networks.get.side_effect = get
        client = mock.MagicMock(return_value=networks)
        return client, network

    def given_mock_client_with_container(self):
        mock_container = mock.MagicMock()

        def get(container_id):
            self.assertEqual('test_container_id', container_id)
            return mock_container

        mock_containers = mock.Mock()
        mock_containers.containers.get = get
        client = mock.MagicMock(return_value=mock_containers)
        return client, mock_container

    def given_client_with_volume(self):
        mock_volume = mock.MagicMock()

        def get(volume_id):
            self.assertEqual('test_id', volume_id)
            return mock_volume

        mock_volumes = mock.Mock()
        mock_volumes.volumes.get.side_effect = get
        client = mock.MagicMock(return_value=mock_volumes)
        return client, mock_volume

    def given_ctx_with_existing_docker_from_repository(self):
        properties = {
            'repository': 'existing'
        }
        return self.given_mock_ctx(properties)

    def given_ctx_with_docker_from_repository(self):
        properties = {
            'repository': 'notexisting'
        }
        return self.given_mock_ctx(properties)

    def given_ctx_with_image(self):
        return self.given_mock_ctx({}, {'image': self.image_id})

    def given_ctx_with_image_and_keep_property(self):
        return self.given_mock_ctx({'keep': True}, {'image': self.image_id})

    def given_ctx_with_relationship(self):
        test_node_id = uuid1()
        rel = mock.Mock()
        rel.type_hierarchy = FROM_IMAGE
        rel.target.instance.runtime_properties = {'image': self.image_id}

        properties = {
            'network_aliases': {},
            'command': None,
            'name': None,
            'port_bindings': {},
            'environment': {},
            'additional_create_parameters': {},
        }
        return MockCloudifyContext(
            node_id=test_node_id,
            properties=properties,
            relationships=[rel]
        )

    def given_ctx_with_container(self):
        return self.given_mock_ctx({}, {'container_id': 'test_container_id'})

    def given_ctx_with_network(self):
        properties = {
            'name': 'test_network',
            'external': False,
            'driver': 'test_driver',
            'options': {'test': 42},
        }
        return self.given_mock_ctx(properties)

    def given_ctx_with_network_id(self, external):
        return self.given_mock_ctx({'external': external}, {'network_id': 'test_network'})

    def given_ctx_with_volume(self, mountpoint):
        properties = {
            'name': 'test_volume',
            'driver': 'test_driver',
            'driver_opts': {'test': 42},
            'source': mountpoint,
        }
        return self.given_mock_ctx(properties)

    def given_ctx_with_existining_volume(self, created):
        properties = {
            'volume_name': 'test_volume',
            'volume_id': 'test_id',
            'volume_created': created,
        }
        return self.given_mock_ctx(test_runtime_properties=properties)

    def given_mock_ctx(self, test_properties=None, test_runtime_properties=None):
        test_node_id = uuid1()
        return MockCloudifyContext(
            node_id=test_node_id,
            properties=test_properties,
            runtime_properties=test_runtime_properties,
        )

    def then_image_is_built(self, ctx):
        self.assertEqual(self.image_id, ctx.instance.runtime_properties['image'])

    def then_client_is_connected(self, client):
        self.assertTrue(client.ping())

    def then_image_is_deleted(self, client):
        self.assertEqual(1, client.return_value.images.remove.call_count)
        self.assertEqual((self.image_id,), client.return_value.images.remove.call_args.args)

    def then_image_is_not_deleted(self, client):
        self.assertFalse(client.return_value.images.remove.called)

    def then_container_is_created(self, client):
        self.assertEqual(1, client.return_value.containers.create.call_count)
        args = {'command': None, 'environment': {}, 'image': self.image_id, 'name': None, 'ports': {}, 'volumes': {}}
        self.assertEqual(args, client.return_value.containers.create.call_args.kwargs)

    def then_container_is_started(self, container):
        self.assertEqual(1, container.start.call_count)

    def then_container_is_stopped(self, container):
        self.assertEqual(1, container.stop.call_count)

    def then_container_is_removed(self, container):
        self.assertEqual(1, container.remove.call_count)

    def then_network_is_created(self, client):
        self.assertEqual(1, client.return_value.networks.get.call_count)
        self.assertEqual(1, client.return_value.networks.create.call_count)
        args = {'name': 'test_network', 'options': {'test': 42}, 'driver': 'test_driver'}
        self.assertEqual(args, client.return_value.networks.create.call_args.kwargs)

    def then_network_is_deleted(self, client, network):
        self.assertEqual(1, client.return_value.networks.get.call_count)
        self.assertEqual(1, network.remove.call_count)

    def then_network_is_not_deleted(self, client, network):
        self.assertEqual(0, client.return_value.networks.get.call_count)
        self.assertEqual(0, network.remove.call_count)

    def then_volume_is_created(self, client):
        self.assertEqual(1, client.return_value.volumes.create.call_count)
        args = {'name': 'test_volume', 'driver_opts': {'test': 42}, 'driver': 'test_driver'}
        self.assertEqual(args, client.return_value.volumes.create.call_args.kwargs)

    def then_volume_is_not_created(self, client):
        self.assertEqual(0, client.return_value.volumes.create.call_count)

    def then_volume_is_deleted(self, client, volume):
        self.assertEqual(1, client.return_value.volumes.get.call_count)
        self.assertEqual(('test_id',), client.return_value.volumes.get.call_args.args)
        self.assertEqual(1, volume.remove.call_count)
        self.assertEqual({'force': True}, volume.remove.call_args.kwargs)

    def then_volume_is_not_deleted(self, client, volume):
        self.assertEqual(0, client.return_value.volumes.get.call_count)
        self.assertEqual(0, volume.remove.call_count)
