import * as fs from 'fs';
import * as path from 'path';
import { createUmi } from '@metaplex-foundation/umi-bundle-defaults';
import { createSignerFromKeypair, signerIdentity } from '@metaplex-foundation/umi';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { create, createCollection, fetchCollection } from '@metaplex-foundation/mpl-core';
import { generateSigner } from '@metaplex-foundation/umi';
import { irysUploader } from '@metaplex-foundation/umi-uploader-irys';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const umi = createUmi('https://api.devnet.solana.com');
const walletFileContent = fs.readFileSync(
  path.join(__dirname, '../central_wallet.json'),
  'utf-8'
);
const secretKeyArray = JSON.parse(walletFileContent);
const keypair = umi.eddsa.createKeypairFromSecretKey(new Uint8Array(secretKeyArray));
const signer = createSignerFromKeypair(umi, keypair);
umi.use(signerIdentity(signer));
umi.use(irysUploader());

const args = process.argv.slice(2);
const METADATA_URI = args[0]; // Expecting the URI as the first argument
const IMAGEURI = args[1];
const NAME = args[2];
const DESCRIPTION = args[3];

console.log(METADATA_URI);
console.log(IMAGEURI);
console.log(NAME);
console.log(DESCRIPTION);

async function fetchMetadata(filePath) {
  return new Promise((resolve, reject) => {
    fs.readFile(filePath, 'utf-8', (err, data) => {
      if (err) {
        console.error('Error reading metadata file:', err);
        return reject(err);
      }
      try {
        const metadata = JSON.parse(data); // Parse the JSON data
        resolve(metadata); // Return the parsed JSON object
      } catch (parseError) {
        console.error('Error parsing JSON:', parseError);
        reject(parseError);
      }
    });
  });
}

async function main() {
  const imagePath = path.join(__dirname, IMAGEURI);

  fs.readFile(imagePath, async (err, imageFile) => {
    if (err) {
      console.error('Error reading image file:', err);
      return;
    }

    try {
      const [imageUri] = await umi.uploader.upload([imageFile]);

      // Fetch and parse the metadata
      const metadata = await fetchMetadata(METADATA_URI);
      
      const assetSigner = generateSigner(umi);

      const assetResult = await create(umi, {
        asset: assetSigner,
        name: NAME,
        uri: metadata.uri, // Use the uri from the fetched metadata
        description: DESCRIPTION || metadata.description // Use description from metadata if provided
      }).sendAndConfirm(umi, { commitment: 'finalized' });

      console.log("Asset created", assetResult);

      // Get mint address and token account address
      const mintAddress = assetResult.mintAddress; // This may vary based on the library version
      const tokenAccountAddress = assetResult.tokenAccountAddress; // Check the exact property names in assetResult

      console.log("Mint Address:", mintAddress);
      console.log("Token Account Address:", tokenAccountAddress);

    } catch (error) {
      if (error.name === 'SendTransactionError') {
        console.error("Error during the NFT creation process:", error.message);

        // Get the transaction logs for debugging
        const logs = error.getLogs ? error.getLogs() : error.transactionLogs;
        console.log("Transaction Logs:", logs);
      } else {
        console.error("Unexpected Error:", error);
      }
    }
  });
}

// Run the main function
main().catch(console.error);
