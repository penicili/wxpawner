import { Sequelize } from 'sequelize';
import { DB_HOST, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_DATABASE_NAME } from './env.js';

const sequelize = new Sequelize(DB_DATABASE_NAME, DB_USERNAME, DB_PASSWORD, {
    host: DB_HOST,
    dialect: 'mysql',
    port: Number(DB_PORT),
    logging: false
});

const connect = async () => {
    try {
        await sequelize.authenticate();
        return Promise.resolve('Connected.');
    } catch (error) {
        throw new Error(error);
    }
}

export { connect, sequelize };

