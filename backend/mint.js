import { createProgrammableNft, mplTokenMetadata } from "@metaplex-foundation/mpl-token-metadata";
import {
  createGenericFile,
  generateSigner,
  percentAmount,
  signerIdentity,
  sol,
} from "@metaplex-foundation/umi";
import { createSignerFromKeypair } from '@metaplex-foundation/umi'
import { transferV1 } from '@metaplex-foundation/mpl-token-metadata'
import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import { irysUploader } from "@metaplex-foundation/umi-uploader-irys";
import { base58 } from "@metaplex-foundation/umi/serializers";
import fs from "fs";
import path from "path";
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import dotenv from 'dotenv';

dotenv.config();


// Get the current directory name
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const createNft = async (name,ImagePath, MetadataPath) => {
  //
  // ** Setting Up Umi **
  //

  const umi = createUmi('https://api.devnet.solana.com')
    .use(mplTokenMetadata())
  .use(
    irysUploader({
      // mainnet address: "https://node1.irys.xyz"
      // devnet address: "https://devnet.irys.xyz"
      address: "https://devnet.irys.xyz",
    })
  );



  // You will need to us fs and navigate the filesystem to
  const walletFile = fs.readFileSync(path.join(__dirname, './keypair.json'));
  const secretKey = JSON.parse(walletFile); // Parse JSON to get the array
  let keypair = umi.eddsa.createKeypairFromSecretKey(new Uint8Array(secretKey));
  const signer = createSignerFromKeypair(umi, keypair);
  umi.use(signerIdentity(signer));



  //
  // ** Upload an image to Arweave **
  //

  // use `fs` to read file via a string path.
  // You will need to understand the concept of pathing from a computing perspective.

  const imageFile = fs.readFileSync(
    path.join(__dirname, ImagePath)
  );

  // Use `createGenericFile` to transform the file into a `GenericFile` type
  // that umi can understand. Make sure you set the mimi tag type correctly
  // otherwise Arweave will not know how to display your image.

  const umiImageFile = createGenericFile(imageFile, `${name}.png`, {
    tags: [{ name: "Content-Type", value: "image/png" }],
  });

  // Here we upload the image to Arweave via Irys and we get returned a uri
  // address where the file is located. You can log this out but as the
  // uploader can takes an array of files it also returns an array of uris.
  // To get the uri we want we can call index [0] in the array.

  console.log("Uploading image...");
  const imageUrl = await umi.uploader.upload([umiImageFile]).catch((err) => {
    throw new Error(err);
  });

  
  const imageUri = imageUrl[0].replace(/arweave\.net/g, 'devnet.irys.xyz');

  //
  // ** Upload Metadata to Arweave **
  //
  const metadataJson = fs.readFileSync(path.join(MetadataPath));
  const metadata = JSON.parse(metadataJson);

  // Replace the image URI in the metadata with the uploaded image URI
  metadata.image = imageUri; // Update image URI
  metadata.properties.files[0].uri = imageUri;
  

  // Call upon umi's uploadJson function to upload our metadata to Arweave via Irys.
  console.log("Uploading metadata...");
  const metadataUrl = await umi.uploader.uploadJson(metadata).catch((err) => {
    throw new Error(err);
  });
  const metadataUri = metadataUrl.replace(/arweave\.net/g, 'devnet.irys.xyz');

  //
  // ** Creating the Nft ** 
  //

  // We generate a signer for the Nft
  const nftSigner = generateSigner(umi);

  // Decide on a ruleset for the Nft.
  // Metaplex ruleset - publicKey("eBJLFYPxJmMGKuFwpDWkzxZeUrad92kZRC5BJLpzyT9")
  // Compatability ruleset - publicKey("AdH2Utn6Fus15ZhtenW4hZBQnvtLgM1YCW2MfVp7pYS5")
  const ruleset = null // or set a publicKey from above

  console.log("Creating Nft...");
  const tx = await createProgrammableNft(umi, {
    mint: nftSigner,
    sellerFeeBasisPoints: percentAmount(0),
    name: metadata.name,
    uri: metadataUri,
    ruleSet: ruleset,
  }).sendAndConfirm(umi);

  // Finally we can deserialize the signature that we can check on chain.
  const signature = base58.deserialize(tx.signature)[0];

  // Log out the signature and the links to the transaction and the NFT.
  console.log("\npNFT Created")
  console.log("View Transaction on Solana Explorer");
  console.log(`https://explorer.solana.com/tx/${signature}?cluster=devnet`);
  console.log("\n");
  console.log("View NFT on Metaplex Explorer");
  console.log(`https://explorer.solana.com/address/${nftSigner.publicKey}?cluster=devnet`);

  const recipientPublicKey = signer.publicKey; // Ensure recipientWallet is a valid public key
  console.log("Transferring NFT...");
  await transferV1(umi,{
    nftSigner,
    authority: currentOwner,
    tokenOwner: currentOwner.publicKey,
    destinationOwner: newOwner.publicKey,
    tokenStandard: TokenStandard.NonFungible,
  }
     
  )
}

// Get command-line arguments
const args = process.argv.slice(2);
const imagePath = args[0];
const metadataPath = args[1]; // Now passing metadata file path
const name = "pon";
createNft(name,imagePath, metadataPath).then((nftSigner) => {
  console.log(`NFT Signer Public Key: ${nftSigner}`);
}).catch((error) => {
  console.error(error);
});

