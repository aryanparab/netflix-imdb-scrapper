import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Get the scripts directory (go up from backend/utils to root, then into scripts)
const SCRIPTS_DIR = path.join(__dirname, '../../scripts');
const ROOT_DIR = path.join(__dirname, '../../');

// Function to find Python executable
function findPythonExecutable() {
  // Try multiple possible locations
  const possiblePaths = [
    path.join(ROOT_DIR, 'venv', 'bin', 'python3'),
    path.join(ROOT_DIR, 'venv', 'bin', 'python'),
    path.join(ROOT_DIR, 'nwr', 'bin', 'python3'),  // If your venv is named 'nwr'
    path.join(ROOT_DIR, 'nwr', 'bin', 'python'),
    'python3',  // System python3
    'python',   // System python
  ];

  for (const pythonPath of possiblePaths) {
    if (existsSync(pythonPath)) {
      console.log(`[Python] Found Python at: ${pythonPath}`);
      return pythonPath;
    }
  }

  // If no specific path found, default to system python3
  console.log(`[Python] Using system python3`);
  return 'python3';
}

export function runPythonScript(scriptName, args = []) {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(SCRIPTS_DIR, scriptName);
    
    console.log(`[Python] Running: ${scriptPath}`);
    console.log(`[Python] Args: ${args.join(' ')}`);

    // Find Python executable
    const pythonPath = findPythonExecutable();
    
    const childProcess = spawn(pythonPath, [scriptPath, ...args], {
      cwd: ROOT_DIR,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1'
      }
    });

    let stdout = '';
    let stderr = '';

    childProcess.stdout.on('data', (data) => {
      const output = data.toString();
      stdout += output;
      console.log(`[Python] ${output.trim()}`);
    });

    childProcess.stderr.on('data', (data) => {
      const output = data.toString();
      stderr += output;
      console.error(`[Python Error] ${output.trim()}`);
    });

    childProcess.on('close', (code) => {
      if (code === 0) {
        console.log(`[Python] Script completed successfully`);
        resolve({ stdout, stderr, code });
      } else {
        console.error(`[Python] Script failed with code ${code}`);
        reject(new Error(`Python script failed with code ${code}\n${stderr}`));
      }
    });

    childProcess.on('error', (error) => {
      console.error(`[Python] Failed to start script:`, error);
      reject(error);
    });
  });
}

export function runPythonScriptStream(scriptName, args = [], onData) {
  const scriptPath = path.join(SCRIPTS_DIR, scriptName);
  const pythonPath = findPythonExecutable();
  
  console.log(`[Python Stream] Running: ${scriptPath}`);

  const childProcess = spawn(pythonPath, [scriptPath, ...args], {
    cwd: ROOT_DIR,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1'
    }
  });

  childProcess.stdout.on('data', (data) => {
    const output = data.toString();
    console.log(`[Python] ${output.trim()}`);
    if (onData) {
      onData({ type: 'stdout', data: output });
    }
  });

  childProcess.stderr.on('data', (data) => {
    const output = data.toString();
    console.error(`[Python Error] ${output.trim()}`);
    if (onData) {
      onData({ type: 'stderr', data: output });
    }
  });

  return childProcess;
}