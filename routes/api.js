import express from 'express';
import challangeController from '../controllers/challange.controller.js';
const router = express.Router();


router.post('/challanges', challangeController.createChallange);

export default router;


