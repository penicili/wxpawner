import express from 'express';
import router from './routes/api.js';

async function init() {
    try {
        const app = express();

        const PORT = process.env.PORT || 3000;

        app.use(express.json());
        app.use('/api', router);

        app.get('/', (req, res) => {
            res.status(200).json({ message: 'Spawner Service is running', data: null });
        });

        app.listen(PORT, () => {
            console.log(`Server is running on http://localhost:${PORT}`);
        });
    } catch (error) {
        console.log(error);
    }
}

init();
