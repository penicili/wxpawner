import express from 'express';
import { spawnContainer, stopContainer } from '../controllers/spawn.controller.js';

const router = express.Router();

router.post('/spawn', spawnContainer);
router.post('/stop', stopContainer);


export default router;
