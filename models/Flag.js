import { Sequelize, DataTypes, Model } from 'sequelize';
import { sequelize } from '../utils/database.js';

class Flag extends Model {}

Flag.init({
    flagString: {
        type: DataTypes.STRING,
        allowNull: false,
    },
    containerId: {
        type: DataTypes.STRING,
        allowNull: false,
    },
    assignedTeam: {
        type: DataTypes.STRING,
        allowNull: true, // kalau null berarti untuk semua team
    },
    status: {
        type: DataTypes.ENUM('active', 'solved'),
        defaultValue: 'active',
        allowNull: false,
    }
},{
    sequelize,
    modelName: 'Flag'
})

export default Flag;