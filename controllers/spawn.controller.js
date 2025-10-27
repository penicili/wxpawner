import { spawn, stopAndRemove } from '../spawner.js';

// Handler to create/spawn a container
export async function spawnContainer(req, res) {
  const body = req.body || {};
  if (!body.image) {
    return res.status(400).json({ ok: false, error: 'image is required' });
  }

  try {
    const info = await spawn(body);
    return res.status(201).json({ ok: true, container: info });
  } catch (err) {
    console.error('spawnContainer error', err);
    return res.status(500).json({ ok: false, error: String(err) });
  }
}

// Handler to stop and remove a container
export async function stopContainer(req, res) {
  const { id } = req.body || {};
  if (!id) return res.status(400).json({ ok: false, error: 'id is required' });

  try {
    await stopAndRemove(id);
    return res.status(200).json({ ok: true, id });
  } catch (err) {
    console.error('stopContainer error', err);
    return res.status(500).json({ ok: false, error: String(err) });
  }
}
