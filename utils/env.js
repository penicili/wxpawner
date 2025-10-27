import dotenv from "dotenv";
dotenv.config();

// DB config
export const DB_HOST= process.env.DB_HOST || 'localhost';
export const DB_PORT= process.env.DB_PORT || '3306';
export const DB_USERNAME= process.env.DB_USERNAME || 'root';
export const DB_PASSWORD= process.env.DB_PASSWORD || '';
export const DB_DATABASE_NAME= process.env.DB_DATABASE_NAME || 'wxpawner';