import ContainerSpawner from '../lib/ContainerSpawner.js';

async function main() {
  // Edit these values to match an image built on your host
  const config = {
    port: 4000, // port where the spawner listens for incoming TCP connections
    image: 'my-local-image:latest', // local image name (must exist locally)
    containerPort: 80, // container's port to bind to host
    reuse: false, // set true to reuse container per source IP
    rateLimit: 0, // ms between allowed spawns per IP when reuse=false
    timeout: 0, // connection timeout (ms), 0 = no limit
    idleTimeout: 60000, // when reuse=true, container idle timeout
  };

  const spawner = new ContainerSpawner(config);

  try {
    await spawner.start();
    console.log('ContainerSpawner started. Press Ctrl+C to stop.');
  } catch (err) {
    console.error('failed to start ContainerSpawner', err);
    process.exit(1);
  }
}

main();
