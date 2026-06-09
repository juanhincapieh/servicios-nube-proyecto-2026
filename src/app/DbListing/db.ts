import { Pool } from 'pg';
import AWS from 'aws-sdk';

const REGION = process.env.AWS_REGION || 'us-east-2';
const DB_HOST = process.env.DB_HOST || '';
const DB_PORT = Number(process.env.DB_PORT) || 5432;
const DB_USER = process.env.DB_USER || '';
const DB_DATABASE = process.env.DB_DATABASE || '';

// Firmante de tokens de autenticación IAM para RDS.
const signer = new AWS.RDS.Signer();

// Genera un token IAM FRESCO en cada conexión. El token caduca a los ~15 min,
// por eso NO se puede fijar uno estático: pg invoca esta función cada vez que
// abre una nueva conexión, obteniendo siempre uno válido.
const getAuthToken = (): Promise<string> =>
  new Promise((resolve, reject) => {
    signer.getAuthToken(
      {
        region: REGION,
        hostname: DB_HOST,
        port: DB_PORT,
        username: DB_USER,
      },
      (err, token) => (err ? reject(err) : resolve(token)),
    );
  });

let mainPool: Pool;

const getPool = () => {
  if (!mainPool) {
    mainPool = new Pool({
      host: DB_HOST,
      port: DB_PORT,
      user: DB_USER,
      database: DB_DATABASE,
      // password como función => pg pide un token nuevo por cada conexión (IAM auth)
      password: getAuthToken,
      application_name: 'ServiciosEnLaNube',
      ssl: {
        rejectUnauthorized: false,
      },
    });
  }

  return mainPool;
};


const getDatabaseData = async () => {
  try {
    const pool = getPool();
    const client = await pool.connect();
    const result = await client.query('SELECT * FROM public.estudiante ORDER BY id DESC');
    client.release();

    return result.rows;
  } catch (error) {
    console.error('Error al consultar la base de datos:', error);
    return [];
  }
};

export default getDatabaseData;
