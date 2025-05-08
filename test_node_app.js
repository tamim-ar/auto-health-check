const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.json({ status: 'healthy' });
});

const port = 3000;
app.listen(port, () => {
    console.log(`Node.js test server running on http://localhost:${port}`);
});
