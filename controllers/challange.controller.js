import { createFlag } from "../services/flag.service.js";
import { spawn } from "../services/spawn.service.js";

export default {
  async createChallange(req, res) {
    // Create a flag
    createFlag(req.flag);
    // Create a challange container instance
    spawn({image:req.image});
    // return
    return res.status(201).json({ 
      message: "Challange created successfully",
      flag: flag,
      image: image
     });
  },
};
