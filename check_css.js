const fs = require('fs');
const css = fs.readFileSync('static/css/style.css', 'utf8');

// Simple CSS validation checks
let errors = [];
let lineNum = 1;
const lines = css.split('\n');

lines.forEach((line, i) => {
    lineNum = i + 1;
    
    // Check for missing semicolons (basic check)
    if (line.trim().includes(':') && 
        !line.trim().endsWith(';') && 
        !line.trim().endsWith('{') && 
        !line.trim().endsWith('}') &&
        !line.trim().startsWith('/*') &&
        !line.trim().startsWith('*') &&
        !line.trim().startsWith('@') &&
        line.trim() !== '' &&
        !line.includes('*/')) {
        errors.push(`Line ${lineNum}: Missing semicolon - '${line.trim()}'`);
    }
    
    // Check for invalid properties
    if (line.includes('justify-content: between')) {
        errors.push(`Line ${lineNum}: Invalid property value 'justify-content: between' - should be 'space-between'`);
    }
    
    // Check for double semicolons
    if (line.includes(';;')) {
        errors.push(`Line ${lineNum}: Double semicolon - '${line.trim()}'`);
    }
    
    // Check for malformed selectors
    if (line.trim().endsWith(',') && i === lines.length - 1) {
        errors.push(`Line ${lineNum}: Dangling comma in selector`);
    }
});

// Count total braces
const totalOpenBraces = (css.match(/{/g) || []).length;
const totalCloseBraces = (css.match(/}/g) || []).length;

if (totalOpenBraces !== totalCloseBraces) {
    errors.push(`Unmatched braces: ${totalOpenBraces} opening, ${totalCloseBraces} closing`);
}

if (errors.length > 0) {
    console.log('CSS ERRORS FOUND:');
    errors.forEach(error => console.log('❌', error));
} else {
    console.log('✅ No obvious CSS syntax errors found');
}
