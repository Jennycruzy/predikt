#!/usr/bin/env node

/**
 * GenLayer Studionet Deployment Script
 * Deploys the PredictionMarket contract to GenLayer Studionet testnet
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// GenLayer Studionet RPC Configuration
const BRADBURY_RPC = 'https://bradbury.genlayer.com/rpc';
const CONTRACT_PATH = path.join(__dirname, 'contracts', 'prediction_market.py');

async function makeRequest(url, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 443,
      path: urlObj.pathname + urlObj.search,
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const req = https.request(options, (res) => {
      let responseData = '';
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      res.on('end', () => {
        try {
          resolve(JSON.parse(responseData));
        } catch (e) {
          resolve(responseData);
        }
      });
    });

    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}

async function deployContract() {
  console.log('🚀 Deploying PredictionMarket to GenLayer Studionet...\n');

  // Read the contract
  let contractCode;
  try {
    contractCode = fs.readFileSync(CONTRACT_PATH, 'utf-8');
    console.log(`✅ Contract loaded from: ${CONTRACT_PATH}\n`);
  } catch (error) {
    console.error(`❌ Failed to read contract: ${error.message}`);
    process.exit(1);
  }

  try {
    // Prepare deployment payload
    const deploymentPayload = {
      jsonrpc: '2.0',
      id: 1,
      method: 'gen_call',
      params: [
        {
          contract_name: 'PredictionMarket',
          contract_code: contractCode,
          network: 'bradbury',
        },
      ],
    };

    console.log('📡 Sending deployment request to Studionet RPC...');
    console.log(`RPC URL: ${BRADBURY_RPC}\n`);

    // Make the RPC call
    const response = await makeRequest(BRADBURY_RPC, 'POST', deploymentPayload);

    if (response.result) {
      const contractAddress = response.result.contract_address || response.result;
      const txHash = response.result.transaction_hash || response.id;

      console.log('✅ Deployment successful!\n');
      console.log('📋 Deployment Details:');
      console.log('─'.repeat(60));
      console.log(`Contract Address: ${contractAddress}`);
      console.log(`Transaction Hash: ${txHash}`);
      console.log(`Network: Studionet Testnet`);
      console.log(`RPC: ${BRADBURY_RPC}`);
      console.log('─'.repeat(60));

      // Save deployment info
      const deploymentInfo = {
        contract_name: 'PredictionMarket',
        network: 'bradbury',
        contract_address: contractAddress,
        transaction_hash: txHash,
        deployment_time: new Date().toISOString(),
        rpc_url: BRADBURY_RPC,
      };

      fs.writeFileSync(
        path.join(__dirname, 'deployment-bradbury.json'),
        JSON.stringify(deploymentInfo, null, 2)
      );

      // Update .env file
      updateEnvFile(contractAddress);

      console.log('\n✅ Deployment info saved to: deployment-bradbury.json');
      return contractAddress;
    } else if (response.error) {
      console.error(`❌ RPC Error: ${response.error.message}`);
      process.exit(1);
    } else {
      console.error('❌ Unexpected response:', response);
      process.exit(1);
    }
  } catch (error) {
    console.error(`❌ Deployment failed: ${error.message}`);
    process.exit(1);
  }
}

function updateEnvFile(contractAddress) {
  const envPath = path.join(__dirname, '.env');
  let envContent = '';

  if (fs.existsSync(envPath)) {
    envContent = fs.readFileSync(envPath, 'utf-8');
  }

  // Update or add NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS
  if (envContent.includes('NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS')) {
    envContent = envContent.replace(
      /NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS=.*/,
      `NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS=${contractAddress}`
    );
  } else {
    envContent += `\n# GenLayer Studionet Contract Address\nNEXT_PUBLIC_PREDICTION_MARKET_ADDRESS=${contractAddress}\n`;
  }

  fs.writeFileSync(envPath, envContent);
  console.log(`✅ Updated .env file with contract address`);
}

// Run deployment
deployContract().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
