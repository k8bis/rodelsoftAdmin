const express = require("express");
const mysql = require("mysql2/promise");
const jwt = require("jsonwebtoken");
const cookieParser = require("cookie-parser");

const app = express();
app.use(express.json());
app.use(cookieParser());

const PORT = process.env.APP2_PORT || 3002;

const dbConfig = {
  host: process.env.MYSQL_HOST || "mysql",
  port: process.env.MYSQL_PORT || 3306,
  user: process.env.MYSQL_USER || "proyecto_user",
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DATABASE || "proyecto_db",
};

const SECRET_KEY = process.env.SECRET_KEY ;
const ALGORITHM = process.env.ALGORITHM || "HS256";

// --- helpers ---

async function getConnection() {
  return mysql.createConnection(dbConfig);
}

function getToken(req) {
  // 1) Header Authorization
  const auth = req.headers.authorization;
  if (auth && auth.startsWith("Bearer ")) {
    return auth.split(" ")[1];
  }

  // 2) Cookie jwt
  if (req.cookies && req.cookies.jwt) {
    return req.cookies.jwt;
  }

  return null;
}

function verifyToken(req, res, next) {
  const token = getToken(req);

  if (!token) {
    return res.status(401).json({ detail: "No token" });
  }

  try {
    const payload = jwt.verify(token, SECRET_KEY, { algorithms: [ALGORITHM] });
    req.user = payload.sub;
    next();
  } catch (err) {
    return res.status(401).json({ detail: "Token inválido o expirado" });
  }
}

function resolveContext(req) {
  let appId = req.headers["x-app-id"] ? Number(req.headers["x-app-id"]) : null;
  let clientId = req.headers["x-client-id"] ? Number(req.headers["x-client-id"]) : null;

  // fallback query params si entran directo
  if (!appId && req.query.app_id) {
    appId = Number(req.query.app_id);
  }

  if (!clientId && req.query.client_id) {
    clientId = Number(req.query.client_id);
  }

  return { appId, clientId };
}

async function validatePermission(username, appId, clientId) {
  const conn = await getConnection();

  try {
    const [rows] = await conn.execute(
      `
      SELECT 1
      FROM permissions p
      JOIN users u ON u.id = p.user_id
      WHERE u.username = ? AND p.app_id = ? AND p.client_id = ?
      LIMIT 1
      `,
      [username, appId, clientId]
    );

    return rows.length > 0;
  } finally {
    await conn.end();
  }
}

// --- routes ---

app.get("/health", async (req, res) => {
  try {
    const conn = await getConnection();
    await conn.execute("SELECT 1");
    await conn.end();

    return res.json({ status: "ok" });
  } catch (err) {
    return res.status(500).json({ detail: `DB error: ${String(err)}` });
  }
});

app.get("/", verifyToken, async (req, res) => {
  try {
    const { appId, clientId } = resolveContext(req);

    if (!appId || !clientId) {
      return res.status(400).json({ detail: "Faltan app_id o client_id" });
    }

    const ok = await validatePermission(req.user, appId, clientId);

    if (!ok) {
      return res.status(403).json({ detail: "Sin permiso para esa app/cliente" });
    }

    return res.json({
      message: "App Hija 2 funcionando!",
      user: req.user,
      app_id: appId,
      client_id: clientId,
      secured: true,
    });
  } catch (err) {
    return res.status(500).json({ detail: String(err) });
  }
});

app.get("/me", verifyToken, async (req, res) => {
  try {
    const { appId, clientId } = resolveContext(req);

    if (appId && clientId) {
      const ok = await validatePermission(req.user, appId, clientId);

      if (!ok) {
        return res.status(403).json({ detail: "Sin permiso para esa app/cliente" });
      }
    }

    return res.json({
      user: req.user,
      app_id: appId || null,
      client_id: clientId || null,
    });
  } catch (err) {
    return res.status(500).json({ detail: String(err) });
  }
});

app.get("/entry", verifyToken, async (req, res) => {
  try {
    const { appId, clientId } = resolveContext(req);

    if (!appId || !clientId) {
      return res.status(400).json({ detail: "Faltan app_id o client_id" });
    }

    const ok = await validatePermission(req.user, appId, clientId);

    if (!ok) {
      return res.status(403).json({ detail: "Sin permiso para esa app/cliente" });
    }

    return res.json({
      ok: true,
      user: req.user,
      app_id: appId,
      client_id: clientId,
      note: "App Hija 2 /entry OK",
    });
  } catch (err) {
    return res.status(500).json({ detail: String(err) });
  }
});

app.listen(PORT, () => {
  console.log(`App Hija 2 corriendo en puerto ${PORT}`);
});