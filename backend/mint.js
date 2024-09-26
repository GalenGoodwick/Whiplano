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

const METADATA = args[0];
const IMAGEURI = args[1];
const NAME = args[2];
const DESCRIPTION = args[3];

console.log(METADATA)
console.log(IMAGEURI)
console.log(NAME)
console.log(DESCRIPTION)


async function main() {
  const imagePath = path.join(__dirname, IMAGEURI);

  fs.readFile(imagePath, async (err, imageFile) => {
    if (err) {
      console.error('Error reading image file:', err);
      return;
    }

    try {
      const [imageUri] = await umi.uploader.upload([imageFile]);
      const uri = await umi.uploader.uploadJson(METADATA);

      const assetSigner = generateSigner(umi);

      const assetResult = await create(umi, {
        asset: assetSigner,
        name: NAME,
        uri: uri,
        description:DESCRIPTION
      }).sendAndConfirm(umi, { commitment: 'finalized' });
      
      console.log("Asset created",assetResult);

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
