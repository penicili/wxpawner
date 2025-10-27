import Docker from 'dockerode';

const docker = new Docker();



// Create and start a container.
// opts: { image, name?, Cmd?, ports?: [{containerPort, hostPort, protocol}] }
export async function createAndStart(opts = {}) {
	const { image, name, Cmd, ports = [] } = opts;
	if (!image) throw new Error('image is required');

	const exposed = {};
	const portBindings = {};
	for (const p of ports) {
		const proto = p.protocol || 'tcp';
		const cp = `${p.containerPort}/${proto}`;
		exposed[cp] = {};
		portBindings[cp] = [
			{ HostPort: String(p.hostPort != null ? p.hostPort : p.containerPort) },
		];
	}

	const createOpts = {
		Image: image,
		name,
		Tty: false,
		ExposedPorts: Object.keys(exposed).length ? exposed : undefined,
		HostConfig: Object.keys(portBindings).length ? { PortBindings: portBindings } : undefined,
	};

	if (Cmd) createOpts.Cmd = Cmd;

	const container = await docker.createContainer(createOpts);
	await container.start();

	const info = await container.inspect();
	return {
		id: info.Id,
		name: info.Name,
		image: info.Config.Image,
		state: info.State,
		networkSettings: info.NetworkSettings,
	};
}

export async function stopAndRemove(containerId) {
	if (!containerId) throw new Error('containerId required');
	const container = docker.getContainer(containerId);
	try {
		// stop may fail if already stopped
		await container.stop({ t: 5 });
	} catch (e) {
		// ignore
	}
	await container.remove({ force: true });
	return { id: containerId };
}

// Convenience: create or pull+start in one step
export async function spawn(opts = {}) {
	const { image } = opts;
	if (!image) throw new Error('image required');
	return createAndStart(opts);
}

