-- Common
SET @MoveTransferToFailedLink = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd';
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';
-- /Common

-- Issue 6020

-- Updated remove unneeded files to remove excess args
UPDATE StandardTasksConfigs SET arguments='"%relativeLocation%" "%fileUUID%"' WHERE pk='49b803e3-8342-4098-bb3f-434e1eb5cfa8';

-- Add remove unneeded files to Transfer, before file ID
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('66aa823d-3b72-4d13-9ad6-c5e6580857b8', 1, 'removeUnneededFiles_v0.0', '"%relativeLocation%" "%fileUUID%"'); -- not in objects/
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('85308c8b-b299-4453-bf40-9ac61d134015', 'a6b1c323-7d36-428e-846a-e7e819423577', '66aa823d-3b72-4d13-9ad6-c5e6580857b8', 'Remove unneeded files');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('5d780c7d-39d0-4f4a-922b-9d1b0d217bca', 'Verify transfer compliance', 'Failed', '85308c8b-b299-4453-bf40-9ac61d134015', 'ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('9cb81a5c-a7a1-43a8-8eb6-3e999923e03c', '5d780c7d-39d0-4f4a-922b-9d1b0d217bca', 0, 'ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='5d780c7d-39d0-4f4a-922b-9d1b0d217bca' WHERE microServiceChainLink='50b67418-cb8d-434d-acc9-4a8324e7fdd2';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='5d780c7d-39d0-4f4a-922b-9d1b0d217bca' WHERE pk='50b67418-cb8d-434d-acc9-4a8324e7fdd2';

-- Add remove unneeded and hidden files to Transfer after extract
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('bdce640d-6e94-49fe-9300-3192a7e5edac', 'Extract packages', 'Failed', 'ef0bb0cf-28d5-4687-a13d-2377341371b5', 'aaa929e4-5c35-447e-816a-033a66b9b90b');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('9a07d5a1-1418-4007-9c7e-55462ca63751', 'bdce640d-6e94-49fe-9300-3192a7e5edac', 0, 'aaa929e4-5c35-447e-816a-033a66b9b90b', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='bdce640d-6e94-49fe-9300-3192a7e5edac' WHERE microServiceChainLink='c5ecb5a9-d697-4188-844f-9a756d8734fa';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='bdce640d-6e94-49fe-9300-3192a7e5edac' WHERE pk='c5ecb5a9-d697-4188-844f-9a756d8734fa';
-- Update for maildir
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('e19f8eed-faf9-4e04-bf1f-e9418f2b2b11', 'Extract packages', 'Failed', 'ef0bb0cf-28d5-4687-a13d-2377341371b5', '22ded604-6cc0-444b-b320-f96afb15d581');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('0ef15153-0d41-4b93-bdb3-4158cec405a3', 'e19f8eed-faf9-4e04-bf1f-e9418f2b2b11', 0, '22ded604-6cc0-444b-b320-f96afb15d581', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='e19f8eed-faf9-4e04-bf1f-e9418f2b2b11' WHERE microServiceChainLink='01b30826-bfc4-4e07-8ca2-4263debad642';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='e19f8eed-faf9-4e04-bf1f-e9418f2b2b11' WHERE pk='01b30826-bfc4-4e07-8ca2-4263debad642';

-- /Issue 6020

-- Issue 5232
-- Update CONTENTdm example to put http:// in front of ContentdmServer
UPDATE MicroServiceChoiceReplacementDic SET replacementDic='{\"%ContentdmServer%\":\"http://111.222.333.444:81\", \"%ContentdmUser%\":\"usernamebar\", \"%ContentdmGroup%\":\"456\"}' WHERE pk='c001db23-200c-4195-9c4a-65f206f817f2';
UPDATE MicroServiceChoiceReplacementDic SET replacementDic='{\"%ContentdmServer%\":\"http://localhost\", \"%ContentdmUser%\":\"usernamefoo\", \"%ContentdmGroup%\":\"123\"}' WHERE pk='ce62eec6-0a49-489f-ac4b-c7b8c93086fd';
-- /Issue 5232

-- Issue 5216

-- Add Chain Choice for 'Add manual normalization metadata'
-- MSCL move to watched dir - terminate
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('38920eaa-09a2-470c-bb3d-791d66ec359c', 0, 'moveSIP_v0.0', '"%SIPDirectory%" "%sharedPath%watchedDirectories/manualNormalizationMetadata/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('fa8b1f81-0d79-4f9a-a888-fc3292f2d992', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '38920eaa-09a2-470c-bb3d-791d66ec359c', 'Move to manual normalization metadata directory');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('b366e9c5-95f6-49f1-957c-a8f7bb601120', 'Normalize', 'Failed', 'fa8b1f81-0d79-4f9a-a888-fc3292f2d992', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('5ce2e89a-ea14-4445-bc92-d287bf02afb3', 'b366e9c5-95f6-49f1-957c-a8f7bb601120', 0, NULL, 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='b366e9c5-95f6-49f1-957c-a8f7bb601120' WHERE microServiceChainLink='91ca6f1f-feb5-485d-99d2-25eed195e330';
-- MSCL move currently processing
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('50ddfe31-de9d-4a25-b0aa-fd802520607b', 'Normalize', 'Failed', '74146fe4-365d-4f14-9aae-21eafa7d8393', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('8008c4a7-bea2-43b0-83ff-b6df0ceb3937', '50ddfe31-de9d-4a25-b0aa-fd802520607b', 0, 'ab0d3815-a9a3-43e1-9203-23a40c00c551', 'Completed successfully');
-- MSCL done MN metadata - Use replacement dict since only one path
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('71d0caff-1257-4843-8df7-82615724d5a5', '9c84b047-9a6d-463f-9836-eafa49743b84', 'a9d91e76-8639-4cfa-9189-54c139cbac60', 'Add manual normalization metadata?');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('a50570ee-2acf-4205-81fd-ddf11c1a6582', 'Normalize', 'Failed', '71d0caff-1257-4843-8df7-82615724d5a5', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('8b65763d-de29-4ce8-b42f-9e244d6d701f', 'a50570ee-2acf-4205-81fd-ddf11c1a6582', 0, '50ddfe31-de9d-4a25-b0aa-fd802520607b', 'Completed successfully');
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ('a9d91e76-8639-4cfa-9189-54c139cbac60', 'a50570ee-2acf-4205-81fd-ddf11c1a6582', 'Metadata entered', '{"%Unused%":"%Unused%"}');
-- MSC manual normalization event detail chain
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES ('e2382ce4-6ee0-4445-aca3-0764ebae94ac', 'a50570ee-2acf-4205-81fd-ddf11c1a6582', 'Manual normalization metadata entry wait');
-- WatchedDir to start up Add manual normalization metadata chain
INSERT INTO WatchedDirectories (pk, watchedDirectoryPath, chain, expectedType) VALUES ('0a621b7d-6cbd-4193-b1d4-b4b90fbc2461', '%watchDirectoryPath%manualNormalizationMetadata/', 'e2382ce4-6ee0-4445-aca3-0764ebae94ac', '76e66677-40e6-41da-be15-709afb334936');

-- /Issue 5216

-- Issue 5955
-- Fix group on METS gen
UPDATE MicroServiceChainLinks SET microserviceGroup = "Prepare AIP" WHERE pk IN ('ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0', '65240550-d745-4afe-848f-2bf5910457c9');
-- /Issue 5955

-- Issue 5803 AIC

-- Create METS.xml file
INSERT INTO StandardTasksConfigs(pk, execute, arguments) VALUES ('1f3f4e3b-2f5a-47a2-8d1c-27a6f1b94b95', 'createMETS_v2.0', '--baseDirectoryPath "%SIPDirectory%" --baseDirectoryPathString "SIPDirectory" --fileGroupIdentifier "%SIPUUID%" --fileGroupType "sipUUID" --xmlFile "%SIPDirectory%METS.%SIPUUID%.xml"');
INSERT INTO TasksConfigs(pk, taskType, taskTypePKReference, description) VALUES ('8ea17652-a136-4251-b460-d50b0c7090eb', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '1f3f4e3b-2f5a-47a2-8d1c-27a6f1b94b95', 'Generate METS.xml document');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('53e14112-21bb-46f0-aed3-4e8c2de6678f', 'Prepare AIC', 'Failed', '8ea17652-a136-4251-b460-d50b0c7090eb', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('27e94795-ae8e-4e7d-942f-346024167c76', '53e14112-21bb-46f0-aed3-4e8c2de6678f', 0, '3ba518ab-fc47-4cba-9b5c-79629adac10b', 'Completed successfully');
-- Create thumbnail dir
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('9e810686-d747-4da1-9908-876fb89ac78e', 'Prepare AIC', 'Failed', 'ea463bfd-5fa2-4936-b8c3-1ce3b74303cf', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('0b689082-e35b-4bc5-b2da-6773398ea6a7', '9e810686-d747-4da1-9908-876fb89ac78e', 0, '53e14112-21bb-46f0-aed3-4e8c2de6678f', 'Completed successfully');
-- Insert create AIC METS MSCL
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('77e6b5ec-acf7-44d0-b250-32cbe014499d', 0, 'createAIC_METS_v1.0', '"%SIPUUID%" "%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('741a09ee-8143-4216-8919-1046571af3e9', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '77e6b5ec-acf7-44d0-b250-32cbe014499d', 'Create AIC METS file');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('142d0a36-2b88-4b98-8a33-d809f667ecef', 'Prepare AIC', 'Failed', '741a09ee-8143-4216-8919-1046571af3e9', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('bff46a44-5493-4217-b858-81e840f1ca8b', '142d0a36-2b88-4b98-8a33-d809f667ecef', 0, '9e810686-d747-4da1-9908-876fb89ac78e', 'Completed successfully');
-- Include default SIP processingMCP
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('d29105f0-161d-449d-9c34-5a5ea3263f8e', 'Prepare AIC', 'Failed', 'f89b9e0f-8789-4292-b5d0-4a330c0205e1', '142d0a36-2b88-4b98-8a33-d809f667ecef');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('1977601d-0a2d-4ccc-9aa6-571d4b6b0804', 'd29105f0-161d-449d-9c34-5a5ea3263f8e', 0, '142d0a36-2b88-4b98-8a33-d809f667ecef', 'Completed successfully');
-- Restructure for compliance
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('0c2c9c9a-25b2-4a2d-a790-103da79f9604', 'Prepare AIC', 'Failed', '3ae4931e-886e-4e0a-9a85-9b047c9983ac', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('b981edfd-d9d8-498f-a7f2-1765d6833923', '0c2c9c9a-25b2-4a2d-a790-103da79f9604', 0, 'd29105f0-161d-449d-9c34-5a5ea3263f8e', 'Completed successfully');
-- Move to processing dir
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('efd15406-fd6c-425b-8772-d460e1e79009', 'Prepare AIC', 'Failed', '74146fe4-365d-4f14-9aae-21eafa7d8393', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('7941ee5a-f093-4cfb-bacc-03dfb7d51e15', 'efd15406-fd6c-425b-8772-d460e1e79009', 0, '0c2c9c9a-25b2-4a2d-a790-103da79f9604', 'Completed successfully');
-- Set permissions
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('f8cb20e6-27aa-44f6-b5a1-dd53b5fc71f6', 'Prepare AIC', 'Failed', 'ad38cdea-d1da-4d06-a7e5-6f75da85a718', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('4aa64bfe-3574-4bd4-8f6f-7c4cb0575f85', 'f8cb20e6-27aa-44f6-b5a1-dd53b5fc71f6', 0, 'efd15406-fd6c-425b-8772-d460e1e79009', 'Completed successfully');
-- Approve/reject AIC
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('81f2a21b-a7a0-44e4-a2f6-9a6cf742b052', '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', NULL, 'Approve AIC');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('6404ce13-8619-48ba-b12f-aa7a034153ac', 'Approve AIC', 'Failed', '81f2a21b-a7a0-44e4-a2f6-9a6cf742b052', @MoveSIPToFailedLink);
-- Reject AIC choice
INSERT INTO MicroServiceChainChoice(pk, choiceAvailableAtLink, chainAvailable) VALUES ('e981fb29-7f93-4719-99ba-f2d22455f3ed', '6404ce13-8619-48ba-b12f-aa7a034153ac', '169a5448-c756-4705-a920-737de6b8d595');
-- Approve AIC choice
INSERT INTO MicroServiceChains(pk, startingLink, description) VALUES ('5f34245e-5864-4199-aafc-bc0ada01d4cd', 'f8cb20e6-27aa-44f6-b5a1-dd53b5fc71f6', 'Approve AIC');
INSERT INTO MicroServiceChainChoice(pk, choiceAvailableAtLink, chainAvailable) VALUES ('bebc5174-09b8-49e6-8dd6-4896e49fdc5e', '6404ce13-8619-48ba-b12f-aa7a034153ac', '5f34245e-5864-4199-aafc-bc0ada01d4cd');

-- Add WatchedDir MSC
INSERT INTO MicroServiceChains(pk, startingLink, description) VALUES ('0766af55-a950-44d0-a79b-9f2bb65f92c8', '6404ce13-8619-48ba-b12f-aa7a034153ac', 'Create AIC');
-- WatchedDirectory
INSERT INTO WatchedDirectories(pk, watchedDirectoryPath, chain, expectedType) VALUES ('aae2a1df-b012-492d-8d84-4fd9bcc25b71', '%watchDirectoryPath%system/createAIC/', '0766af55-a950-44d0-a79b-9f2bb65f92c8', '76e66677-40e6-41da-be15-709afb334936');

-- Add Part of AIC to Dublin Core
ALTER TABLE Dublincore ADD isPartOf longtext;

-- Updated bagit command to put metadata/ in the payload too
UPDATE StandardTasksConfigs SET arguments='create "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%METS.%SIPUUID%.xml" "%SIPDirectory%thumbnails/" "%SIPDirectory%metadata/" --writer filesystem --payloadmanifestalgorithm "sha512"' WHERE pk='045f84de-2669-4dbc-a31b-43a4954d0481';

-- Add sipType to SIPs table
ALTER TABLE SIPs ADD sipType varchar(8);

-- IndexAIP and storeAIP uses sipType
UPDATE StandardTasksConfigs SET arguments='"%SIPUUID%" "%SIPName%" "%SIPDirectory%%AIPFilename%" "%SIPType%"' WHERE pk='81f36881-9e54-4c75-a5b2-838cfb2ca228';
UPDATE StandardTasksConfigs SET arguments='"%AIPsStore%" "%SIPDirectory%%AIPFilename%" "%SIPUUID%" "%SIPName%" "%SIPType%"' WHERE pk='7df9e91b-282f-457f-b91a-ad6135f4337d';

-- /Issue 5803 AIC
