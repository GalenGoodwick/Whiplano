import {
  createProgrammableNft,
  mplTokenMetadata,
} from "@metaplex-foundation/mpl-token-metadata";
import {
  updateV1,
  fetchMetadataFromSeeds,
} from "@metaplex-foundation/mpl-token-metadata";

import {
  createGenericFile,
  generateSigner,
  percentAmount,
  signerIdentity,
  sol,
} from "@metaplex-foundation/umi";
import { createSignerFromKeypair } from "@metaplex-foundation/umi";
import {
  transferV1,
  createV1,
  TokenStandard,
  mintV1,
  fetchDigitalAsset,
} from "@metaplex-foundation/mpl-token-metadata";
import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import { irysUploader } from "@metaplex-foundation/umi-uploader-irys";
import { base58 } from "@metaplex-foundation/umi/serializers";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";
import dotenv from "dotenv";

dotenv.config();
const args = process.argv.slice(2);

const metadatastring = args[0]; // Now passing metadata file path
const metadata = JSON.parse(metadatastring);

const upload_metadata = async (metadata) => {
  //
  // ** Setting Up Umi **
  //

  const umi = createUmi("https://api.devnet.solana.com")
    .use(mplTokenMetadata())
    .use(
      irysUploader({
        // mainnet address: "https://node1.irys.xyz"
        // devnet address: "https://devnet.irys.xyz"
        address: "https://devnet.irys.xyz",
      })
    );

  // You will need to us fs and navigate the filesystem to
  const secretKeyString = process.env.CENTRAL_WALLET_KEY;
  if (!secretKeyString) {
    throw new Error("CENTRAL_WALLET_KEY is not set in environment variables");
  }
  // Parse the stringified array to get the array of numbers (the secret key)
  const secretKey = JSON.parse(secretKeyString);
  let keypair = umi.eddsa.createKeypairFromSecretKey(new Uint8Array(secretKey));
  const signer = createSignerFromKeypair(umi, keypair);
  umi.use(signerIdentity(signer));

  // Call upon umi's uploadJson function to upload our metadata to Arweave via Irys.
  const metadataUrl = await umi.uploader.uploadJson(metadata).catch((err) => {
    throw new Error(err);
  });
  const metadataUri = metadataUrl.replace(/arweave\.net/g, "devnet.irys.xyz");
  console.log(JSON.stringify({ uri: metadataUri }));
};

// Get command-line arguments
upload_metadata(metadata)
  .then((nftSigner) => {})
  .catch((error) => {
    console.error(error);
  });
