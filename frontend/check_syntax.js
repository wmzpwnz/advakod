const fs = require('fs');

const testFiles = [
    'src/components/__tests__/ResilientWebSocket.test.js',
    'src/components/__tests__/ChatIntegration.test.js'
];

testFiles.forEach(testFile => {
    if (fs.existsSync(testFile)) {
        try {
            const content = fs.readFileSync(testFile, 'utf8');
            console.log(`✅ ${testFile} - File exists and readable`);
        } catch (e) {
            console.log(`❌ ${testFile} - Error: ${e.message}`);
        }
    } else {
        console.log(`❌ ${testFile} - File not found`);
    }
});