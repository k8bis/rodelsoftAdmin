const express = require("express");
const jwt = require("jsonwebtoken");
const pool = require("./db");
require("dotenv").config();

const app = express();
const PORT = process.env.APP2_PORT || 3000;
const SECRET_KEY = process.env.SECRET_KEY;

// Middleware global
app.use(express.json());

// Middleware JWT
function verifyToken(req, res, next) {
  const authHeader = req.headers["authorization"];
  if (!authHeader?.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Token requerido" });
  }

  const token = authHeader.split(" ")[1];
  try {
    const payload = jwt.verify(token, SECRET_KEY);
    req.username = payload.sub;
    next();
  } catch (err) {
    return res.status(401).json({ error: "Token inválido o expirado" });
  }
}

// Endpoint raíz
app.get("/", (req, res) => res.json({ message: "App Hija 2 funcionando!" }));

// Permisos según usuario JWT
app.get("/permissions", verifyToken, async (req, res) => {
  const username = req.username;
  try {
    const [rows] = await pool.query(`
      SELECT a.id AS app_id, a.name AS app,
             c.id AS client_id, c.name AS client
      FROM permissions p
      JOIN applications a ON p.app_id = a.id
      JOIN clients      c ON p.client_id = c.id
      JOIN users        u ON p.user_id = u.id
      WHERE u.username = ?
      ORDER BY a.name, c.name
    `, [username]);
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});


app.get('/me', (req, res) => {
  const client = req.header('x-client-name');
  res.json({ cliente_seleccionado: client });
});

app.get("/entry", verifyToken, async (req, res) => {
  const username = req.username;
  const appId = Number(req.header("x-app-id"));
  const clientId = Number(req.header("x-client-id"));
  if (!appId || !clientId) 
    return res.status(400).json({ error: "Faltan X-App-Id o X-Client-Id" });
  try {
    const [rows] = await pool.query(`
      SELECT 1
      FROM permissions p
      JOIN users u ON u.id = p.user_id
      WHERE u.username = ? AND p.app_id = ? AND p.client_id = ?
      LIMIT 1
    `, [username, appId, clientId]);
    if (!rows.length) return res.status(403).json({ error: "Sin permiso" });

    return res.json({
      ok: true,
      user: req.username,
      app_id: appId,
      client_id: clientId,
      note: "App2 /entry OK",
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Iniciar servidor
app.listen(PORT, () => console.log(`App Hija 2 corriendo en puerto ${PORT}`));

