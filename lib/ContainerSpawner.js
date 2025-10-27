import net from 'net';
import Docker from 'dockerode';
import getPort from 'get-port';
import { setTimeout as delay } from 'node:timers/promises';

// Minimal console-based logger to avoid extra deps
const logger = {
  info: (...args) => console.log('[info]', ...args),
  warn: (...args) => console.warn('[warn]', ...args),
  error: (...args) => console.error('[error]', ...args),
};

function createDockerClient() {
  const env = process.env;
  if (env.DOCKER_HOST) {
    try {
      const hostUrl = env.DOCKER_HOST;
      if (hostUrl.startsWith('tcp://')) {
        const withoutProto = hostUrl.replace('tcp://', '');
        const [host, portStr] = withoutProto.split(':');
        const port = portStr ? parseInt(portStr, 10) : 2375;
        return new Docker({ host, port });
      }
      return new Docker({ socketPath: env.DOCKER_HOST });
    } catch (e) {
      console.error('Invalid DOCKER_HOST, falling back to platform defaults', e);
    }
  }

  if (process.platform === 'win32') {
    return new Docker({ socketPath: '//./pipe/docker_engine' });
  }

  return new Docker({ socketPath: '/var/run/docker.sock' });
}

class ContainerSpawner {
  constructor(config) {
    ContainerSpawner.validateConfig(config);
    this.config = Object.assign(
      {
        reuse: false,
        rateLimit: 0,
        timeout: 0,
        idleTimeout: 60 * 1000,
      },
      config
    );

    this.rateLimitMap = {}; // ip -> nextAllowedTime
    this.containerMap = new Map(); // ip -> containerInfo
    this.docker = createDockerClient();
    this.server = null;
  }

  static validateConfig(config) {
    if (!config) throw new Error('config required');
    const required = ['port', 'image', 'containerPort'];
    for (const k of required) {
      if (!(k in config)) throw new Error(`missing config.${k}`);
    }
  }

  async _handleRateLimit(client) {
    if (this.config.rateLimit <= 0) return;
    const addr = client.remoteAddress || 'unknown';
    const now = Date.now();
    const next = (this.rateLimitMap[addr] || 0);
    if (next > now) {
      const wait = next - now;
      logger.info(`rate-limited ${addr}, waiting ${wait}ms`);
      await delay(wait);
    }
    this.rateLimitMap[addr] = Date.now() + this.config.rateLimit;
  }

  async _setupContainer() {
    const availablePort = await getPort({ host: '127.0.0.1' });
    const portDesc = `${this.config.containerPort}/tcp`;

    const container = await this.docker.createContainer({
      Image: this.config.image,
      HostConfig: {
        PortBindings: {
          [portDesc]: [
            {
              HostIP: '127.0.0.1',
              HostPort: String(availablePort),
            },
          ],
        },
      },
      ExposedPorts: {
        [portDesc]: {},
      },
    });

    await container.start();

    // wait briefly for services inside container to be ready
    await delay(200);

    return { container, availablePort };
  }

  _doTcpProxy(client, port) {
    return new Promise((resolve) => {
      client.on('error', () => resolve());
      client.on('close', () => resolve());

      const service = new net.Socket();

      service.connect(port, '127.0.0.1', () => {
        client.pipe(service);
        service.pipe(client);
      });

      service.on('error', () => resolve());
      service.on('close', () => resolve());

      if (this.config.timeout) {
        setTimeout(() => resolve(), this.config.timeout);
      }
    });
  }

  static async _cleanupContainer(container) {
    try {
      await container.stop();
    } catch (e) {
      // ignore
    }
    try {
      await container.remove();
    } catch (e) {
      // ignore
    }
  }

  async _clientHandler(client) {
    client.on('error', () => {});

    const addr = client.remoteAddress || 'unknown';
    logger.info(`new connection from ${addr}`);

    if (!this.config.reuse) await this._handleRateLimit(client);

    if (client.destroyed) {
      logger.warn('client disconnected early');
      return;
    }

    let containerInfo = null;
    if (this.config.reuse) containerInfo = this.containerMap.get(addr) || null;

    if (!containerInfo) {
      containerInfo = await this._setupContainer();
      containerInfo.activeConnections = 0;
      if (this.config.reuse) this.containerMap.set(addr, containerInfo);
      containerInfo.shortId = containerInfo.container.id.substring(0, 12);
      logger.info(`container ${addr}/${containerInfo.shortId} created`);
    }

    if (containerInfo.idleTimeout) {
      clearTimeout(containerInfo.idleTimeout);
      containerInfo.idleTimeout = null;
    }

    containerInfo.activeConnections += 1;

    await this._doTcpProxy(client, containerInfo.availablePort);

    containerInfo.activeConnections -= 1;

    if (!this.config.reuse) {
      logger.info(`session ${addr}/${containerInfo.shortId} ending`);
      await ContainerSpawner._cleanupContainer(containerInfo.container);
    } else if (containerInfo.activeConnections === 0) {
      containerInfo.idleTimeout = setTimeout(async () => {
        logger.info(`container ${addr}/${containerInfo.shortId} idle timeout`);
        await ContainerSpawner._cleanupContainer(containerInfo.container);
        this.containerMap.delete(addr);
      }, this.config.idleTimeout);
    }
  }

  start() {
    return new Promise((resolve, reject) => {
      try {
        this.server = net.createServer(this._clientHandler.bind(this));
        const host = '0.0.0.0';
        this.server.on('listening', () => {
          logger.info(`listening on ${host}:${this.config.port}`);
          resolve();
        });
        this.server.on('error', (e) => reject(e));
        this.server.listen(this.config.port, host);
      } catch (e) {
        reject(e);
      }
    });
  }

  stop() {
    return new Promise((resolve) => {
      if (this.server) {
        this.server.close(() => {
          logger.info('server shutting down');
          resolve();
        });
      } else {
        resolve();
      }
    });
  }
}

export default ContainerSpawner;
