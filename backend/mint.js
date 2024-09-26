import { publicKey, some, generateSigner, percentAmount, keypairIdentity, createSignerFromKeypair } from "@metaplex-foundation/umi";
import {
  fetchCandyMachine,
  fetchCandyGuard,
  mplCandyMachine,
  create,
  setCandyMachineAuthority,
  setCandyGuardAuthority,
} from '@metaplex-foundation/mpl-candy-machine'
// Use the RPC endpoint of your choice.

import {
  createNft,
  TokenStandard,
} from '@metaplex-foundation/mpl-token-metadata'

async function manageCandyMachine() {
  const umi = createUmi('https://api.devnet.solana.com');
  umi.use(mplCandyMachine());
  console.log("E")
  // Create the Collection NFT.
  const collectionUpdateAuthority = generateSigner(umi)
  const collectionMint = generateSigner(umi)

  const myKeypair = umi.eddsa.createKeypairFromSecretKey(new Uint8Array([15,96,246,96,168,118,204,153,41,122,14,70,62,175,75,122,122,10,202,172,60,76,153,241,33,130,7,194,51,240,101,221,168,191,211,242,139,189,173,204,59,2,253,72,101,253,176,40,31,52,98,56,62,115,191,231,79,53,241,119,160,252,8,129]));
  const myKeypairSigner = createSignerFromKeypair(umi, myKeypair);
  umi.use(keypairIdentity(myKeypairSigner));

  await createNft(umi, {
    mint: collectionMint,
    authority: collectionUpdateAuthority,
    name: 'My Collection NFT',
    uri: 'https://example.com/path/to/some/json/metadata.json',
    sellerFeeBasisPoints: percentAmount(9.99, 2), // 9.99%
    isCollection: true,
  }).sendAndConfirm(umi)

  console.log(umi.identity.publicKey);

  // Create the Candy Machine.
  const candyMachine = generateSigner(umi);
  const creatorA = generateSigner(umi).publicKey;

  await(await create(umi, {
    candyMachine,
    collectionMint: collectionMint.publicKey,
    collectionUpdateAuthority,
    tokenStandard: TokenStandard.NonFungible,
    sellerFeeBasisPoints: percentAmount(9.99, 2), // 9.99%
    itemsAvailable: 5,
    creators: [
      {
        address: umi.identity.publicKey,
        verified: true,
        percentageShare: 100,
      },
    ],
    configLineSettings: some({
      prefixName: '',
      nameLength: 32,
      prefixUri: '',
      uriLength: 200,
      isSequential: false,
    }),
  })).sendAndConfirm(umi)


  const candyMachinePublicKey = candyMachine.publicKey
  console.log('pub key: ' + candyMachinePublicKey)
  
  // // Fetch the Candy Machine.
  const cm = await fetchCandyMachine(umi, candyMachinePublicKey)
  const candyGuard = await fetchCandyGuard(umi, cm.mintAuthority)

  console.log(cm.publicKey) // The public key of the Candy Machine account.
  console.log(cm.mintAuthority) // The mint authority of the Candy Machine which, in most cases, is the Candy Guard address.
  console.log(cm.data.itemsAvailable) // Total number of NFTs available.
  console.log(cm.itemsRedeemed) // Number of NFTs minted.
}

manageCandyMachine()