import { Pool } from 'pg';
import AWS from 'aws-sdk';

const REGION = process.env.AWS_REGION || 'us-east-2';
const DB_HOST = process.env.DB_HOST || '';
const DB_PORT = Number(process.env.DB_PORT) || 5432;
const DB_USER = process.env.DB_USER || '';
const DB_DATABASE = process.env.DB_DATABASE || '';

// Credenciales explícitas desde el .env (sin depender de la cadena por defecto
// ni del rol de instancia). Si son de larga duración, AWS_SESSION_TOKEN va vacío.
const credentials = new AWS.Credentials({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
  ...(process.env.AWS_SESSION_TOKEN
    ? { sessionToken: process.env.AWS_SESSION_TOKEN }
    : {}),
});

// Firmante de tokens IAM para RDS, usando esas credenciales.
const signer = new AWS.RDS.Signer({
  region: REGION,
  hostname: DB_HOST,
  port: DB_PORT,
  username: DB_USER,
  credentials,
});

// Token IAM FRESCO en cada conexión (caduca ~15 min). pg llama esta función
// por cada cliente nuevo, así que siempre obtiene uno válido.
const getAuthToken = (): Promise<string> =>
  new Promise((resolve, reject) => {
    signer.getAuthToken({}, (err, token) => (err ? reject(err) : resolve(token)));
  });

let mainPool: Pool;

const getPool = () => {
  if (!mainPool) {
    mainPool = new Pool({
      host: DB_HOST,
      port: DB_PORT,
      user: DB_USER,
      database: DB_DATABASE,
      password: getAuthToken, // password como función => token IAM por conexión
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
