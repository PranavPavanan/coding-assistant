#!/usr/bin/env node
/**
 * Test runner script for the RAG GitHub Assistant frontend.
 * 
 * This script provides a convenient way to run all frontend tests with proper
 * configuration and reporting.
 */

const { execSync } = require('child_process');
const path = require('path');

function runCommand(command, description) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`Running: ${description}`);
  console.log(`Command: ${command}`);
  console.log(`${'='.repeat(60)}`);
  
  try {
    const output = execSync(command, { 
      encoding: 'utf8', 
      stdio: 'pipe',
      cwd: path.dirname(__filename)
    });
    
    console.log(`✅ ${description} - PASSED`);
    if (output) {
      console.log('Output:');
      console.log(output);
    }
    return true;
  } catch (error) {
    console.log(`❌ ${description} - FAILED`);
    if (error.stderr) {
      console.log('Error:');
      console.log(error.stderr.toString());
    }
    if (error.stdout) {
      console.log('Output:');
      console.log(error.stdout.toString());
    }
    return false;
  }
}

function main() {
  console.log('🧪 RAG GitHub Assistant Frontend - Test Runner');
  console.log('='.repeat(60));
  
  const results = [];
  
  // Run unit tests
  console.log('\n🔬 Running Unit Tests...');
  const unitTests = [
    ['npm run test:unit', 'Component Unit Tests'],
  ];
  
  for (const [command, description] of unitTests) {
    const success = runCommand(command, description);
    results.push([description, success]);
  }
  
  // Run integration tests
  console.log('\n🔗 Running Integration Tests...');
  const integrationTests = [
    ['npm run test:integration', 'User Workflow Tests'],
  ];
  
  for (const [command, description] of integrationTests) {
    const success = runCommand(command, description);
    results.push([description, success]);
  }
  
  // Run all tests together
  console.log('\n🚀 Running All Tests Together...');
  const allTestsSuccess = runCommand('npm run test', 'All Tests');
  results.push(['All Tests', allTestsSuccess]);
  
  // Run tests with coverage
  console.log('\n📊 Running Tests with Coverage...');
  const coverageSuccess = runCommand('npm run test:coverage', 'Coverage Report');
  results.push(['Coverage Report', coverageSuccess]);
  
  // Print summary
  console.log('\n' + '='.repeat(60));
  console.log('📋 TEST SUMMARY');
  console.log('='.repeat(60));
  
  let passed = 0;
  let failed = 0;
  
  for (const [description, success] of results) {
    const status = success ? '✅ PASSED' : '❌ FAILED';
    console.log(`${status} - ${description}`);
    if (success) {
      passed++;
    } else {
      failed++;
    }
  }
  
  console.log(`\nTotal: ${passed + failed} test suites`);
  console.log(`Passed: ${passed}`);
  console.log(`Failed: ${failed}`);
  
  if (failed === 0) {
    console.log('\n🎉 All tests passed! The frontend is ready for deployment.');
    process.exit(0);
  } else {
    console.log(`\n⚠️  ${failed} test suite(s) failed. Please fix the issues before deploying.`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}
