const fs = require("fs");
const path = require("path");

function updateEnv(key, value) {
  const envPath = path.join(__dirname, "../../.env");
  let envContent = fs.existsSync(envPath) ? fs.readFileSync(envPath, "utf8") : "";
  const regex = new RegExp(`^${key}=.*`, "m");
  if (regex.test(envContent)) {
    envContent = envContent.replace(regex, `${key}=${value}`);
  } else {
    envContent += `\n${key}=${value}`;
  }
  fs.writeFileSync(envPath, envContent);
  console.log(`✅ Updated .env: ${key}=${value}`);
}

async function deployToken() {
  const [deployer] = await ethers.getSigners();
  console.log("\n🚀 Deploying MockUSDL with:", deployer.address);
  console.log("💳 Balance:", ethers.formatEther(await deployer.provider.getBalance(deployer.address)), "ETH");

  const MockUSDL = await ethers.getContractFactory("MockUSDL");
  const token = await MockUSDL.deploy();
  await token.waitForDeployment();

  const address = await token.getAddress();
  console.log("✅ MockUSDL deployed to:", address);
  updateEnv("NEXT_PUBLIC_MOCK_USDL_ADDRESS", address);
  
  return address;
}

async function deployFactory(tokenAddress) {
  const [deployer] = await ethers.getSigners();
  console.log("\n🚀 Deploying BetFactory with:", deployer.address);

  const BetFactory = await ethers.getContractFactory("BetFactory");
  const factory = await BetFactory.deploy(tokenAddress);
  await factory.waitForDeployment();

  const address = await factory.getAddress();
  console.log("✅ BetFactory deployed to:", address);
  updateEnv("NEXT_PUBLIC_BET_FACTORY_ADDRESS", address);

  return address;
}

async function main() {
  console.log("Starting full deployment on Base Sepolia...");
  const tokenAddr = await deployToken();
  await deployFactory(tokenAddr);
  console.log("\n🎉 Deployment Complete!");
}

main().catch(console.error);
