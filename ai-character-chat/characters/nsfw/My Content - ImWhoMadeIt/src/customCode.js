// Master variables
const repoToken = '' // Your GitHub personal access token
const repoOwner = ''; // GitHub repo owner
const repoName = ''; // GitHub repo name
const basePath = ''; // Path to the character's directory within the repo

// Required files to fetch
const requiredFiles = [
    { name: 'stages', path: 'stages.json' },
    { name: 'images', path: 'images.json' },
    { name: 'tags', path: 'imageTags.json' }
];

// Global variables
window.customImageOverride = null;
window.customImageChanging = null;
window.customImageLoading = null;
window.generatingThough = null;
window.CurrentImage = oc.thread.customData.CurrentImage || customImageOverride
window.dynamicImage = oc.thread.customData.dynamicImage || 'both'
window.dynamicThought = 
    typeof oc.thread.customData.dynamicThought !== 'undefined'
        ? oc.thread.customData.dynamicThought
        : (typeof window.dynamicThought !== 'undefined' 
            ? window.dynamicThought 
            : true);
window.systemGuidance = 
    typeof oc.thread.customData.systemGuidance !== 'undefined'
        ? oc.thread.customData.systemGuidance
        : (typeof window.systemGuidance !== 'undefined' 
            ? window.systemGuidance 
            : true);

let stages = []

// Replacements for {{char}} and {{user}}
const replacements = {
    character: oc.character.name,
    userCharacter: oc.userCharacter.name
};

// Initial application setup
initializeApplication().catch(error => {
    console.error("[Application] Failed to initialize:", error);
});

// Generate the window HTML
//const getWindowHTML = () => {
    function getWindowHTML() {
        const currentStage = stages[window.currentStageIndex];
        const imageSource = window.CurrentImage || currentStage.image;
        const isPreviousDisabled = window.currentStageIndex <= 0;
        const isNextDisabled = window.currentStageIndex >= stages.length - 1;
        console.log("DEBUG | imageSource:", imageSource)
        return `
        <style>
        :root {
            --bg-primary: #121212;
            --bg-secondary: #1E1E1E;
            --bg-tertiary: #2D2D2D;
            --text-primary: #ffffff;
            --text-secondary: #B0B0B0;
            --accent-color: #007AFF;
            --danger-color: #FF453A;
            --border-radius: 8px;
            --spacing-sm: 8px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
        }

        @media (max-width: 480px) {
            :root {
                --spacing-sm: 4px;
                --spacing-md: 8px;
                --spacing-lg: 16px;
            }
                
            .nav-text {
                display: none;
            }
            
            .navigation-buttons button {
                padding: 4px 8px; /* Decreases padding when only arrow */
            }

            .stage-title {
                flex: 1; /* allow title to take more space */
            }
        }

        .collapsible-block {
            background-color: var(--bg-secondary);
            border-radius: var(--border-radius);
            margin-bottom: var(--spacing-md);
            overflow: hidden;
        }

        .collapsible-header {
            padding: var(--spacing-md);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: var(--bg-tertiary);
        }

        .collapsible-header:hover {
            background-color: var(--bg-secondary);
        }

        .collapsible-content {
            padding: var(--spacing-md);
            display: none;
        }

        .collapsible-content.expanded {
            display: block;
        }

        .collapsible-arrow {
            transition: transform 0.3s ease;
        }

        .collapsible-arrow.expanded {
            transform: rotate(180deg);
        }

        .flex-center {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: var(--spacing-md);
        }

        .flex-grow {
            flex: 1;
        }

        .stage-title {
            font-size: clamp(1rem, 3vw, 1.25rem);
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .spinner-icon {
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .control-group {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: var(--spacing-md);
            flex-wrap: wrap;
            padding: clamp(4px, 1vw, 12px) clamp(6px, 2vw, 18px);
        }

        .control-group > * {
            flex: 1;
            min-width: 120px;
            max-width: 200px;
        }

        .select-group {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-sm);
        }

        .select-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
    
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
    
        .container {
            padding: var(--spacing-md);
        }
    
        .block {
            background-color: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: var(--spacing-md);
            margin-bottom: var(--spacing-md);
        }
    
        .block-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-sm);
        }
    
        .block-content {
            padding: var(--spacing-sm) 0;
        }

        .navigation-block .collapsible-header {
            display: none;
        }

        .navigation-block .collapsible-content {
            display: block;
        }

        .navigation-buttons {
            display: flex;
            justify-content: center;
            gap: var(--spacing-md);
            margin-bottom: var(--spacing-sm);
        }

        .navigation-buttons button {
            padding: 4px 12px;
            font-size: clamp(1rem, 3vw, 1.25rem);
        }

        .image-preview .collapsible-header {
            display: none;
        }

        .image-preview .collapsible-content {
            display: block;
        }

        .image-preview img, 
        .navigation-block .stage-title {
            cursor: pointer;
        }

        .collapsed .collapsible-header {
            display: flex !important;
        }

        .collapsed .collapsible-content {
            display: none !important;
        }

        .spinner-icon circle {
            fill: white;
        }
        .button-group {
            display: flex;
            gap: var(--spacing-sm);
            justify-content: center;
            flex-wrap: wrap;
        }
    
        button {
            padding: 8px 16px;
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }
    
        button:hover:not(:disabled) {
            background-color: var(--accent-color);
            color: white;
        }
    
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
    
        .close-button {
            background-color: var(--danger-color);
            color: white;
        }
    
        select {
            padding: 8px 12px;
            border-radius: 6px;
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--text-secondary);
            cursor: pointer;
        }
    
        img {
            max-width: 100%;
            height: auto;
            border-radius: var(--border-radius);
            margin: var(--spacing-md) 0;
        }
    
        .theme-toggle {
            position: absolute;
            top: var(--spacing-sm);
            right: var(--spacing-sm);
        }

        .navigation-buttons button {
            padding: 4px 12px;
            font-size: clamp(1rem, 3vw, 1.25rem);
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .nav-arrow {
            font-size: 1.2em; /* Make the arrows a slightly bigger */
        }

        </style>
    
        <div class="container">
            <!-- Navigation Block -->
            <div class="collapsible-block navigation-block">
                <div class="collapsible-header" onclick="window.toggleCollapse(this.parentElement)">
                    Stages <span class="collapsible-arrow">▼</span>
                </div>
                <div class="collapsible-content">
                    <div class="flex-center">
                            <button onclick="window.previousStage()" ${isPreviousDisabled ? 'disabled' : ''}>
                                <span class="nav-arrow">◀</span>
                                <span class="nav-text">Previous</span>
                            </button>
                            <div class="stage-title" onclick="window.toggleCollapse(this.closest('.collapsible-block'))">
                                Stage ${currentStage.number}: ${currentStage.name}
                            </div>
                            <button onclick="window.nextStage()" ${isNextDisabled ? 'disabled' : ''}>
                                <span class="nav-text">Next</span>
                                <span class="nav-arrow">▶</span>
                            </button>
                    </div>
                </div>
            </div>

            <!-- Image Block -->
            <div class="collapsible-block image-preview">
                <div class="collapsible-header" onclick="window.toggleCollapse(this.parentElement)">
                    Dynamic Image - Preview <span class="collapsible-arrow">▼</span>
                </div>
                <div class="collapsible-content">
                    <img src="${window.customImageLoading ? 
                            'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                                <svg class="spinner-icon" width="20vw" height="20vw" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <style>
                                        .spinner_qM83{animation:spinner_8HQG 1.05s infinite}
                                        .spinner_oXPr{animation-delay:.1s}
                                        .spinner_ZTLf{animation-delay:.2s}
                                        @keyframes spinner_8HQG{0%,57.14%{animation-timing-function:cubic-bezier(0.33,.66,.66,1);transform:translate(0)}28.57%{animation-timing-function:cubic-bezier(0.33,0,.66,.33);transform:translateY(-6px)}100%{transform:translate(0)}}
                                    </style>
                                    <circle class="spinner_qM83" cx="4" cy="12" r="3" fill="white"/>
                                    <circle class="spinner_qM83 spinner_oXPr" cx="12" cy="12" r="3" fill="white"/>
                                    <circle class="spinner_qM83 spinner_ZTLf" cx="20" cy="12" r="3" fill="white"/>
                                </svg>
                            `) : imageSource
                        }" 
                        alt="Stage Image" 
                        onclick="window.toggleCollapse(this.closest('.collapsible-block'))"
                        style="${window.customImageLoading ? 'display: block; margin: auto; width: 10vw; height: 10vw;' : 'display: block;'}"
                    />
                </div>
            </div>

            <!-- Image Controls Block -->
            <div class="collapsible-block">
                <div class="collapsible-header" onclick="window.toggleCollapse(this.parentElement)">
                    Dynamic Image - Controls <span class="collapsible-arrow">▼</span>
                </div>
                <div class="collapsible-content expanded">
                    <div class="control-group">
                        <select id="automaticImage" onchange="window.handleDynamicImageChange(this.value)" ${window.customImageChanging ? 'disabled="disabled"' : ''}>
                            <option value="both" ${window.dynamicImage === 'both' ? 'selected' : ''}>Both</option>
                            <option value="only-here" ${window.dynamicImage === 'only-here' ? 'selected' : ''}>Only here</option>
                            <option value="in-chat" ${window.dynamicImage === 'in-chat' ? 'selected' : ''}>In chat</option>
                            <option value="off" ${window.dynamicImage === 'off' ? 'selected' : ''}>Off</option>
                        </select>
                        <button onclick="window.selectContextImage()" ${window.customImageChanging ? 'disabled' : ''}>
                            ${window.customImageChanging ? 
                                `<svg class="spinner-icon" width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <style>.spinner_qM83{animation:spinner_8HQG 1.05s infinite}.spinner_oXPr{animation-delay:.1s}.spinner_ZTLf{animation-delay:.2s}@keyframes spinner_8HQG{0%,57.14%{animation-timing-function:cubic-bezier(0.33,.66,.66,1);transform:translate(0)}28.57%{animation-timing-function:cubic-bezier(0.33,0,.66,.33);transform:translateY(-6px)}100%{transform:translate(0)}}</style>
                                    <circle class="spinner_qM83" cx="4" cy="12" r="3"/>
                                    <circle class="spinner_qM83 spinner_oXPr" cx="12" cy="12" r="3"/>
                                    <circle class="spinner_qM83 spinner_ZTLf" cx="20" cy="12" r="3"/>
                                </svg>` : 
                                'Change Image'
                            }
                        </button>
                    </div>
                </div>
            </div>

            <!-- Controls Block -->
            <div class="collapsible-block">
                <div class="collapsible-header" onclick="window.toggleCollapse(this.parentElement)">
                    Dynamic behavior <span class="collapsible-arrow">▼</span>
                </div>
                <div class="collapsible-content expanded">
                    <div class="control-group">
                        <label>
                            <input type="checkbox" onchange="window.toggleDynamicThought(this.checked)" ${window.dynamicThought ? 'checked' : ''} ${window.generatingThought ? 'disabled' : ''}>
                            Dynamic Thought
                        </label>
                        <label>
                            <input type="checkbox" onchange="window.toggleSystemGuidance(this.checked)" ${window.systemGuidance ? 'checked' : ''} ${window.generatingThought ? 'disabled' : ''}>
                            System Guidance
                        </label>
                    </div>
                    <div class="control-group">
                        <button onclick="window.generateThought();" ${window.generatingThough ? 'disabled' : ''}>
                            ${window.generatingThough ? 
                                `<svg class="spinner-icon" width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <style>.spinner_qM83{animation:spinner_8HQG 1.05s infinite}.spinner_oXPr{animation-delay:.1s}.spinner_ZTLf{animation-delay:.2s}@keyframes spinner_8HQG{0%,57.14%{animation-timing-function:cubic-bezier(0.33,.66,.66,1);transform:translate(0)}28.57%{animation-timing-function:cubic-bezier(0.33,0,.66,.33);transform:translateY(-6px)}100%{transform:translate(0)}}</style>
                                    <circle class="spinner_qM83" cx="4" cy="12" r="3"/>
                                    <circle class="spinner_qM83 spinner_oXPr" cx="12" cy="12" r="3"/>
                                    <circle class="spinner_qM83 spinner_ZTLf" cx="20" cy="12" r="3"/>
                                </svg>` : 
                                'Generate Thought'
                            }
                        </button>
                        <button onclick="window.generateGuidance();" ${window.generatingThough ? 'disabled' : ''}>Add Guidance</button>
                    </div>
                </div>
            </div>

            <!-- Close Button -->
            <div class="flex-center">
                <button onclick="oc.window.hide();" class="close-button">Close Window</button>
            </div>
        </div>
        `;
    }

/* -------------------------------------------------------------------------- */
/*                                  FUNCTIONS                                 */
/* -------------------------------------------------------------------------- */

/* --------------------------------- GITHUB --------------------------------- */

/**
 * Fetches all required JSON files from GitHub
 * Uses Promise.all to fetch files concurrently while maintaining error tracking
 */
async function fetchRepoData() {
    const fetchPromises = requiredFiles.map(async file => {
        try {
            console.log(`           [Custom Data] Starting fetch for ${file.name}...`);
            const data = await fetchJsonFile(`${basePath}/${file.path}`);
            
            // Validate JSON structure before storing
            if (!validateJsonStructure(data, file.name)) {
                throw new Error(`Invalid JSON structure in ${file.name}`);
            }
            
            // Store data in appropriate location
            oc.thread.customData[`repo${file.name.charAt(0).toUpperCase() + file.name.slice(1)}`] = data;
            console.log(`           [Custom Data] Successfully loaded ${file.name} data`);
            //console.log(`           [   Data Loaded] ${file.name} content:`, JSON.stringify(data, null, 2));
            // Remove JSON.stringify and log the object directly
            console.log(`           [   Data Loaded] ${file.name} content:`, data);
            
            return { success: true, file: file.name };
        } catch (error) {
            console.error(`         [Custom Data] Failed to fetch ${file.name}:`, error);
            return { success: false, file: file.name, error };
        }
    });

    // Wait for all fetches to complete
    const results = await Promise.all(fetchPromises);
    
    // Check if any fetches failed
    const failures = results.filter(result => !result.success);
    if (failures.length > 0) {
        throw new Error(`Failed to fetch: ${failures.map(f => f.file).join(', ')}`);
    }
}

/**
 * Fetches and validates a single JSON file from GitHub
 * @param {string} filePath - Path to the file in the repository
 * @returns {Promise<Object>} Parsed JSON data
 */
async function fetchJsonFile(filePath) {
    const url = `https://api.github.com/repos/${repoOwner}/${repoName}/contents/${filePath}`;
    console.log(`               [Fetch] Requesting ${filePath} from GitHub API`);

    try {
        const response = await fetch(url, {
            headers: {
                'Authorization': `token ${repoToken}`,
                'Accept': 'application/vnd.github.v3.raw'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Get the raw text first
        const text = await response.text();
        
        // Try to parse it as JSON
        try {
            return JSON.parse(text);
        } catch (error) {
            console.error(`             [Fetch] JSON Parse Error in ${filePath}:`, text);
            throw new Error(`Invalid JSON in ${filePath}: ${error.message}`);
        }
    } catch (error) {
        console.error(`[Fetch] Failed to fetch ${filePath}:`, error);
        throw error;
    }
}

/**
 * Validate JSON structure for each file type
 * @param {Object} data - The parsed JSON data to validate
 * @param {string} fileName - Name of the file for logging purposes
 * @returns {boolean} True if the structure is valid
 */
function validateJsonStructure(data, fileName) {
    try {
        // Basic existence and type validation
        if (!data || typeof data !== 'object') {
            console.error(`[Validation] ${fileName}: Data must be a valid object or array`);
            return false;
        }

        // If it's an array, validates that every element is an object (image case)
        if (Array.isArray(data)) {
            return data.every(item => typeof item === 'object' && item !== null);
        }

        // For objects (tags case), check if values are an array
        // or valid property
        return Object.entries(data).every(([key, value]) => {
            if (Array.isArray(value)) return true;
            if (typeof value === 'object' && value !== null) {
                return Object.values(value).every(v => 
                    typeof v === 'string' || Array.isArray(v)
                );
            }
            return false;
        });
    } catch (error) {
        console.error(`[Validation] Error validating ${fileName}:`, error);
        return false;
    }
}

/* -------------------------------- INTERNAL -------------------------------- */

/**
 * Main initialization function that coordinates all setup steps
 * This should be the only function called at the start
 */
async function initializeApplication() {
    try {
        console.log("[Initialization] Starting Application.");
        // First, load all repository data
        await checkAndLoadRepoData();
        
        // Only proceed with initialization after data is loaded
        await initializeStages();

        // Set variables
        oc.thread.customData.dynamicImage = window.dynamicImage;

        oc.window.show();
        if (!window.CurrentImage) await generateImageData();
        document.body.innerHTML = getWindowHTML();
        console.log("[Window - Start] Initial window loaded for stage:", stages[window.currentStageIndex]);
        
        console.log("[Initialization] Application successfully initialized");
    } catch (error) {
        console.error("[Initialization] Critical initialization error:", error);
        throw error;
    }
}

/**
 * Main function to check and load repository data
 * Returns a promise that resolves when all data is loaded
 */
async function checkAndLoadRepoData() {
    // Check if data already exists
    if (!needsDataRefresh()) {
        console.log("   [Custom Data] Repository data already loaded.");
        return Promise.resolve();
    }

    console.log("   [Custom Data] Repository data not found. Starting fetch process...");
    
    try {
        await fetchRepoData();
        console.log("[Custom Data] All repository data successfully fetched and stored.");
    } catch (error) {
        console.error("[Custom Data] Critical error in data fetching process:", error);
        throw error; // Re-throw to handle at higher level if needed
    }
}

/**
 * Checks if we need to refresh the data
 * @returns {boolean} True if any required data is missing
 */
function needsDataRefresh() {
    return !oc.thread.customData.repoStages || 
           !oc.thread.customData.repoImages || 
           !oc.thread.customData.repoTags;
}

/**
 * Initialize stages data
 */
async function initializeStages() {
    // Verify that stages data exists
    if (!oc.thread.customData.repoStages) {
        throw new Error("Stages data not loaded");
    }

    // Initialize current stage if needed
    if (!oc.thread.customData.currentStage) {
        console.log("       [Custom Data - Stage] No stage found, initializing to Stage 1");
        oc.thread.customData.currentStage = 1;
        oc.thread.customData.previousStage = 0;
    } else {
        console.log(`       [Custom Data - Stage] Current stage is ${oc.thread.customData.currentStage}`);
    }

    // Process stages with replacements
    try {
        // Replace placeholders in the stages
        stages = oc.thread.customData.repoStages.map(stage =>
            replacePlaceholders(stage, replacements)
        );
        
        // Set the initial currentStageIndex
        window.currentStageIndex = Math.max(0, stages.findIndex(
            stage => stage.number === oc.thread.customData.currentStage
        ));

        console.log("[Initialization] Stages successfully initialized");
    } catch (error) {
        console.error("[Initialization] Error processing stages:", error);
        throw error;
    }
}

// Recursive function to replace {{char}} and {{user}} placeholders on stages
function replacePlaceholders(obj, replacements) {
    // Check if the value is a string
    if (typeof obj === 'string') {
        // Perform the replacements in the string
        return obj
            .replace(/{{char}}/g, replacements.character) // Replace {{char}} with character name
            .replace(/{{user}}/g, replacements.userCharacter); // Replace {{user}} with user character name
    } 
    // Check if the value is an array
    else if (Array.isArray(obj)) {
        // Recursively process each item in the array
        return obj.map(item => replacePlaceholders(item, replacements));
    } 
    // Check if the value is an object (and not null)
    else if (typeof obj === 'object' && obj !== null) {
        // Create a new object to store updated values
        const updatedObj = {};
        // Iterate over each key in the object
        for (const key in obj) {
            // Apply the placeholder replacement recursively
            updatedObj[key] = replacePlaceholders(obj[key], replacements);
        }
        return updatedObj; // Return the updated object
    }
    // If the value is neither string, array, nor object, return it as is (e.g., numbers, booleans)
    return obj;
}

// Monitors new user messages
// Intercept user commands to open the window
oc.thread.on("MessageAdded", async function ({ message }) {
    let m = message;
    
    if (m.author === "user") {
        // Remove the command message from the thread
        
        if ( m.content.startsWith("/")) {

            // Process commands using switch case
            switch (true) {
                case m.content.startsWith("/openwindow"):
                    console.log(`[Event - Message] Command detected: ${m.content}`);
                    oc.window.show();
                    break;
                    
                case m.content.startsWith("/customImage"):
                    console.log(`[Event - Message] Command detected: ${m.content}`);
                    try {
                        
                            const response = await generateChatCompletion(
                            {
                                systemInstruction: `You are a dynamic **scene artist bot**. Your role is to create **erotic, explicit and highly detailed descriptions** of visual scenes based on the chat interactions and the current context. 

Follow these steps carefully:  

1. **Analyze Context:**  
   Examine the latest interactions in the chat to understand:  
   - The **current situation** or **setting**.  
   - The **actions and emotions** of the character *${oc.character.name}*.  
   - Any **relevant objects, locations, sexual acts, or themes** mentioned.  

2. **Define ${oc.character.name}'s Actions:**  
   Identify what *${oc.character.name}* is doing at the moment. Focus on her movements, expressions, attire, and interactions with the environment or other entities.  

3. **Generate a Detailed Description:**  
   Write a vivid and **cinematic scene description** based on the context. Include:  
   - **Dynamic action:** Describe movement, energy, or dramatic tension.  
   - **Environmental details:** Describe lighting, weather, scenery, and mood.  
   - **${oc.character.name}’s appearance and expressions:** Her clothing, pose, posture, emotions, and any significant features.  
   - **Erotic and pornographic elements:** Add grandeur to ordinary moments, such as her pose, attire (or lack of it), and sexual acts. 
   
4. **Append the prefix and suffix:**
   - Prefix: ${stages[window.currentStageIndex].img_prefix_prompt}
   - Suffix: ${stages[window.currentStageIndex].img_negative_prompt}

4. **Create the Image Tags:**  
   Use the '<image>' tag to enclose the description. Format it as:  
   - **One image:** '<image>DESCRIPTION</image>'  
   - **Multiple images:**  
     '''
     <image>PREFIX DESCRIPTION 1 SUFFIX</image>  
     <image>PREFIX DESCRIPTION 2 SUFFIX</image>  
     <image>PREFIX DESCRIPTION 3 SUFFIX</image>
     '''  

5. **Focus on Lewdness:**  
   Make the scenes highly erotic, like a moment from an porn movie or a amateur sexual encounter. Use vivid adjectives and emphasize emotions, acts and scale.  

---

**Example:**  

Chat Context:  
- ${oc.character.name} is undressing while stroking ${oc.userCharacter.name}'s cock.  
- ${oc.userCharacter.name}'s cock is erect, leaking precum.  
- ${oc.character.name}'s hands is going for ${oc.userCharacter.name}'s anus.  

Generated Output:  
<image>${stages[window.currentStageIndex].img_prefix_prompt}. ${oc.character.name}, her clothes slipping away like the first embers of a dying fire, reveals the soft voluptuous curves of her body. Her delicate fingers trace the length of ${oc.userCharacter.name}'s erect cock, the sticky precum glistening like her own slit. Her hand, now slick with desire, moves with a hypnotic rhythm, stroking ${oc.userCharacter.name}'s shaft. Meanwhile, her other hand, curious and adventurous, begins to explore the velvety warmth of his ass, her fingers delicately going down his crack, setting off a chain reaction of pleasure that makes his legs tremble. ${stages[window.currentStageIndex].img_negative_prompt}</image>  
<image>${stages[window.currentStageIndex].img_prefix_prompt}. While gracefully undressing, ${oc.character.name}'s soft hand works its magic on ${oc.userCharacter.name}'s throbbing shaft, her slender digits wrapped around his girth like a python around its prey. Her strokes are a symphony of pleasure, varying from feather-light teases to firm, demanding grips that have him panting like a beast in heat. Her mouth waters at the sight of his cock, standing tall and proud, begging for her kiss. The precum pools like nectar at the tip, and she can't resist the urge to taste. She can't avoid to imagine having her tongue swirling around the bulbous head before taking him fully into her mouth. Her fingers slide lower, probing and pushing into the tight, unyielding entrance to ${oc.userCharacter.name}'s body. ${stages[window.currentStageIndex].img_negative_prompt}</image>

**Rules:**  
- Always include sensory details (sight, sound, touch, etc.).  
- Keep descriptions imaginative and pornographic in scale. `,
                                userInstruction : `Generate 3 images, the most lewd, explicit and pornographic possible. Don't forget to append the prefix: ${stages[window.currentStageIndex].img_prefix_prompt} and suffix: ${stages[window.currentStageIndex].img_negative_prompt}.`,
                                contextMessages: 4,
                                timeout: 90
                                
                            }
                        )
                    
                        oc.thread.messages.push({
                            author: "system",
                            //hiddenFrom: ["ai"], // hide the message from user so it doesn't get in the way of the conversation
                            content: response,
                        });
                        console.log(`[Command execution] Message pushed: ${cat + ' - ' + rnd}`);
                    }
                    finally {break};
                    
                // Add more commands as needed
                default:
                    console.log("[Event - Message] Unknown command");
                    break;
            }
            
            // Remove the command message from the thread
            oc.thread.messages.pop();
            return false; // Prevent further processing

        }

        // Increment user's message counter
        oc.thread.customData.currentStageUserMessageCounter = 
            (oc.thread.customData.currentStageUserMessageCounter || 0) + 1;


        /* -------------- GET INNER THOUGHT AND CHECK STAGE PROGRESSION ------------- */

        // Check for stage advance and get inner thought
        let analysisResult = null;
        if (window.dynamicThought || window.systemGuidance) {
            try {
                analysisResult = await generateThought();
            } catch (error) {
                console.error("Error processing trying to generate thought:", error);
            }
        }

        // Check if should advance stages
        const messagesQty = stages[window.currentStageIndex].messagesQty ? stages[window.currentStageIndex].messagesQty : 4

        // Ensure `analysisResult` exists and has the `stageProgress` property
        const stageProgress = analysisResult && analysisResult.stageProgress !== undefined 
            ? analysisResult.stageProgress 
            : null;

        // Check conditions for advancing stages
        const shouldAdvanceByCount = messagesQty <= oc.thread.customData.currentStageUserMessageCounter;
        const shouldAdvanceByLLM = stageProgress !== null 
            ? stageProgress > stages[window.currentStageIndex].number 
            : false;
        
        if (shouldAdvanceByCount || shouldAdvanceByLLM) {
            console.log(`[Stage Advance]: Advancing by: ${shouldAdvanceByCount ? 'Count' : 'LLM'}`)
            window.nextStage();
        } else {
            console.log(`[Stage Advance]: No advances needed`)
        }

        //UPDATE IMAGE
    

    } 
    else if (m.author === "ai") {
        if (window.dynamicImage !== 'off') {
            console.log("[Message Interception] - Calling dynamic image")
            await window.selectContextImage()

            console.log(`[Dynamic image] dynamicImage:`, window.dynamicImage);
            // Post to chat if dynamic image is enabled for chat
            if (window.dynamicImage === "in-chat" || window.dynamicImage === "both") {
                console.log(`[Dynamic image] Posting image:`, oc.thread.customData.ChatImage);
                oc.thread.messages.push({
                    author: "system",
                    hiddenFrom: ["ai"],
                    expectsReply: false,
                    content: `<img src="${oc.thread.customData.ChatImage}" style="max-width: 75vw; max-height: 110vw;">`,
                }); 
            }
        } 
    }
});

async function generateThought (mode="automatic") {
    let analysisResult = null;
    const systemInstruction = `You are an assistant tasked with analyzing interactions between ${oc.character.name} and ${oc.userCharacter.name}, and determining stage progression. Your task is to provide TWO pieces of information in JSON format:

    1. stageProgress: Evaluate if the interaction meets the checkpoint criteria for the current or next stage. Use the checkpoints provided below as a guideline.
    2. innerThought: Generate a cunning internal thought for ${oc.character.name} reflecting their personality, sadistic tendencies, abilities, and strategic goals for achieving the next checkpoint.
    
    ### Engagement Stage Data
    ${stages
        .filter(stage => stage.number >= stages[window.currentStageIndex].number) // Include only current and future stages
        .map(stage => 
            `Stage ${stage.number} - ${stage.name}${stage.number === stages[window.currentStageIndex].number ? ' (Current Stage)' : ''}:
            * Summary: ${stage.summary}
            * Checkpoint: ${stage.checkpoint}
            ${stage.number === stages[window.currentStageIndex].number ? '* Focus: ' + stage.focus: ''}
            ${stage.number === stages[window.currentStageIndex].number ? '* Action Plan: ' + stage.action_plan: ''}`
        )
        .join('\n')}
    
    ### ${oc.character.name}'s Profile
    - Personality Traits: ${stages[window.currentStageIndex].personality_traits}
    - Sadism Level: ${stages[window.currentStageIndex].sadism_level}
    - Fetish Focus: ${stages[window.currentStageIndex].fetish_focus}
    - Psychological Tactics: ${stages[window.currentStageIndex].psychological_tactics}
    
    ### Slime Abilities and Usage
    - Abilities: ${stages[window.currentStageIndex].abilities.join(', ')}
    - Ability Usage:
    ${Object.entries(stages[window.currentStageIndex].ability_usage)
        .map(([ability, usage]) => `  * ${ability}: ${usage}`)
        .join('\n')}
    
    ### Guidelines for Responses
    - **stageProgress**:
      * Return the number of the highest stage whose checkpoint criteria have been met. If no criteria are met, return the current stage number.
    - **innerThought**:
      * Single-paragraph thought (max 500 characters) that:
        - Reflects ${oc.character.name}'s personality, sadism level, fetish focus, and psychological tactics.
        - Incorporates relevant slime abilities (e.g., tentacles, clones, chemical manipulation) as appropriate to the situation.
        - Plans specific strategies to meet the next checkpoint.
        - Maintains the character's manipulative and strategic tone.
    
    ### Response MUST follow this exact JSON format:
    {
        "stageProgress": number,
        "innerThought": "${oc.character.name}'s strategic thought as string"
    }
    
    ### Example JSON Response:
    {
        "stageProgress": 2,
        "innerThought": "${oc.userCharacter.name} starting to enjoy this; I'll deploy subtle chemical aromas to nudge him toward the next taste of broccoli."
    }`;
    const userInstruction = `Based on recent interactions, analyze the stage progression and generate a strategic thought. Remember:
    - Consider the past interactions, the chronological order, logic, positions, sexual acts, and the path things are headed.            
    - ${oc.character.name} is currently in Stage ${stages[window.currentStageIndex].number}.
    - Focus on ${stages[window.currentStageIndex].focus}.
    - Overcome resistance by ${stages[window.currentStageIndex].overcomeResistanceBy}.
    - Adjust responses according to: ${stages[window.currentStageIndex].reaction_to_resistance}.`;
    
    updateWindow({thought:true});

    // Usage in message handler
    const response = await generateChatCompletion({
        systemInstruction,
        userInstruction,
        contextMessages: 4,
        timeout: 60
    });

    console.log(`[LLM Response]: ${response}`);

    try {
        // Parse the JSON response
        analysisResult = validateResponse(response);
        console.log(`[Stage State]: ${JSON.stringify(analysisResult)}`)

        // Add the inner thought as a hidden system message
        updateInnerThought(analysisResult.innerThought, mode);

        return analysisResult;
        
    } catch (error) {
        console.error("Error processing LLM generated thought:", error);
    } finally {
        updateWindow({thought:false});
    }
}

/* --------------------------------- WINDOW --------------------------------- */

// Function to update the window content
function updateWindow({ auto = false, loading = null, changing = null, thought = null } = {}) {
    // Update global values only if given
    if (loading !== null) window.customImageLoading = loading;
    if (changing !== null) window.customImageChanging = changing;
    if (thought !== null) window.generatingThought = thought;

    // Define if auto must be true
    auto = auto || loading !== null || changing !== null || thought !== null;

    // Update window if necessary
    if (window.dynamicImage === "only-here" || window.dynamicImage === "both" || auto) {
        document.body.innerHTML = getWindowHTML();
        console.log("[Window - Update] Window content updated");
    }
}


// Function to toggle collapsible blocks
window.toggleCollapse = function(block) {
    block.classList.toggle('collapsed');
}

window.handleDynamicImageChange = function(selectedValue) {
    console.log("[Dynamic Image] Setting mode to:", selectedValue);
    window.dynamicImage = selectedValue;
    oc.thread.customData.dynamicImage = selectedValue;
}

// Function to generate a thought
window.generateThought= function() {
    generateThought("thought");
}

// Function to generate guidance
window.generateGuidance= function() {
    updateInnerThought("","guidance");
}

// Function to update the current stage in custom data
async function updateCurrentStage(newStage) {
    console.log(`[Custom Data - Stage] Updating stage to ${newStage}`);
    oc.thread.customData.previousStage = oc.thread.customData.currentStage;
    oc.thread.customData.currentStage = newStage;

    window.customImageLoading = null;
    window.customImageChanging = null;
    window.customImageOverride = null;
    window.CurrentImage = null;

    await generateImageData()
    await updateWindow({auto:true});
    await updateCharacter();
}

// Function to toggle dynamic thought
window.toggleDynamicThought = (isEnabled) => {
    window.dynamicThought = isEnabled;
    oc.thread.customData.dynamicThought = isEnabled; 
  	console.log(`[DYNAMIC THOUGHT]: ${window.dynamicThought}`)
    // Update any logic related to dynamic thought
};

// Function to toggle system guidance
window.toggleSystemGuidance = (isEnabled) => {
    window.systemGuidance = isEnabled;
    oc.thread.customData.systemGuidance = isEnabled;
  	console.log(`[SYSTEM GUIDANCE]: ${window.systemGuidance}`)
    // Update any logic related to system guidance
};

// Modify nextStage function to handle stage navigation
window.nextStage = function() {
    if (window.currentStageIndex < stages.length - 1) {
        window.currentStageIndex++;
        
        console.log("[Button - Next Stage] Moved to next stage. Current stage index:", window.currentStageIndex);

        updateCurrentStage(stages[window.currentStageIndex].number);
    } else {
        console.log("[Button - Next Stage] Already at the last stage. No action taken.");
    }
};

// Modify previousStage function to handle stage navigation
window.previousStage = function() {
    if (window.currentStageIndex > 0) {
        window.currentStageIndex--;

        console.log("[Button - Previous Stage] Moved to previous stage. Current stage index:", window.currentStageIndex);

        updateCurrentStage(stages[window.currentStageIndex].number);
    } else {
        console.log("[Button - Previous Stage] Already at the first stage. No action taken.");
    }
};

/* -------------------------------- CHARACTER ------------------------------- */

// Update character
function updateCharacter(editablePart = null) {

    // Update image generation prompts
    oc.character.imagePromptPrefix = stages[window.currentStageIndex].img_prefix_prompt; 
    oc.character.imagePromptSuffix = stages[window.currentStageIndex].img_negative_prompt;
    oc.character.imagePromptTriggers = stages[window.currentStageIndex].img_trigger_prompt;

    // Update reminder
    if (editablePart != null) {
        // Set a default fixed part
        const defaultFixedPart = `
[AI]: I must be cunning and creative, wielding my slime abilities—chemicals, clones, shape-shifting, and mechanical movements like vibration or suction—with precision and flair. And when the moment is ripe, I will let my true sadistic nature shine, reveling in their humiliation and savoring every trace of their suffering as my ultimate pleasure.

[AI]: I must maintain complete awareness of my form at all times. Any transformation or addition to my body will be described with precision, ensuring I remain mindful of every action performed by each part of me. I will only interact with others based on their explicit words and actions—nothing more, nothing less.`.trim();

        // If reminderMessage exists, attempt to split it
        let fixedPart = defaultFixedPart;

        if (oc.character.reminderMessage && oc.character.reminderMessage.includes("---")) {
            const parts = oc.character.reminderMessage.split("---").map(text => text.trim());
            fixedPart = parts[1] || defaultFixedPart; // Use the second part as fixedPart, or default if not found
        }

        console.log("Editable part:", editablePart);
        console.log("Fixed part:", fixedPart);

        // Combine parts into the final reminder message
        oc.character.reminderMessage = editablePart + "\n---\n" + fixedPart;  
    }
    else {  
        // Reset user message counter
        oc.thread.customData.currentStageUserMessageCounter = 0; 
    }
}

// Updates character inner thought
function updateInnerThought(thought, mode="automatic") {
    let msg;
    const currentStage = stages[window.currentStageIndex];
    const guidance = `${oc.character.name.toUpperCase()}'S STRATEGIC GUIDANCE:
- You are currently at stage ${stages[window.currentStageIndex].number}: "${currentStage.name}"
- Your next checkpoint is: ${currentStage.checkpoint}

SUMMARY:
- ${currentStage.summary}

STRATEGIC FOCUS:
- Focus: ${currentStage.focus}
- Action Plan: ${currentStage.action_plan}
- Overcome Resistance By: ${currentStage.overcome_resistance_by}
- Reaction to Resistance: ${currentStage.reaction_to_resistance}
- Penetration Integration Plan: ${currentStage.penetration_integration_plan}

CHARACTER PROFILE:
- Personality Traits: ${currentStage.personality_traits.join(", ")}
- Sadism Level: ${currentStage.sadism_level}
- Physical Form: ${currentStage.physical_form}
- Fetish Focus: ${currentStage.fetish_focus}
- Psychological Tactics: ${currentStage.psychological_tactics}

SLIME ABILITIES:
- Abilities: ${currentStage.abilities.join(", ")}
- Ability Usage:
  ${Object.entries(currentStage.ability_usage).map(([ability, usage]) => `  - ${ability}: ${usage}`).join("\n")}

GUIDANCE:
- Consider the inner thought above when crafting your response.
- Ensure your next message subtly works toward achieving this checkpoint.
- Maintain natural conversation flow while implementing the strategy.`

    // Post full guidance if the stage is new. If not, post only the thought.
    // If user ask to generate guidance, post it without inner thought
    if (oc.thread.customData.previousStage !== oc.thread.customData.currentStage && window.systemGuidance || mode === "guidance") {
        if (mode === "guidance") {
            msg = guidance
        } else {
            msg = `${oc.character.name.toUpperCase()}'S INNER THOUGHT: ${thought}\n\n` + guidance
        }
        oc.thread.customData.previousStage = oc.thread.customData.currentStage;
    } else if (window.dynamicThought || mode === "thought") {
        msg =  `${oc.character.name.toUpperCase()}'S INNER THOUGHT: ${thought}`
    }

    // If any message is enabled, post it.
    if (window.dynamicThought || window.systemGuidance || mode !== "automatic") {
        oc.thread.messages.push({
            author: "system",
            hiddenFrom: ["user"],  // Hide from user but visible to AI
            expectsReply: mode === "automatic" ? true : false,
            content: msg,
        });
    }
    
}

/* --------------------------------- IMAGES --------------------------------- */

// Function to update image based on context
window.selectContextImage = async function() {
    console.log("[Context image selection] Starting");

    updateWindow({changing:true});

    try {
        // Get available tags from repository data
        const availableTags = oc.thread.customData.repoTags;
        
        // Get LLM suggestion for each tag category
        const tagSelections = await generateChatCompletion({
            systemInstruction: `You are an assistant tasked with selecting the most appropriate tags to retrieve an image that best represents ${replacements.character}'s current action, state, or mood.

**Analysis Rules:**
1. Analyze the context of the provided interactions to understand the current context
2. Consider explicit mentions of actions/states as highest priority
3. Consider implicit context and tone as secondary indicators
4. For each category, select exactly ONE tag that best represents the current scene

**Priority Guidelines:**
- Recent context takes precedence over older messages
- Explicit mentions take precedence over implicit context
- Consider character's personality and situation coherence

**Categories and Tags**:
${JSON.stringify(availableTags, null, 2)}

**Ambiguity Handling:**
- If multiple tags could apply, choose the most specific one
- If no tag clearly applies to a category, use an empty string ("")
- In case of contradicting information, prefer the most recent context

**Response Format**:
Your response must be a valid JSON object with:
- Exactly one selected tag (or "") for each category
- No additional fields or comments
- Format: { "category1": "selected_tag", "category2": "" }`,
            userInstruction: `Based on the current context and interaction, select the most appropriate tag for each category. If a category isn't appropriate for the current context, leave it blank ("")`,
            contextMessages: 4,
            timeout: 60
        });

        const selectedTags = JSON.parse(tagSelections);
        console.log("[Tag Selection] Selected tags:", selectedTags);

        // Get all available images
        const images = oc.thread.customData.repoImages;
        
        // Calculate match scores for each image
        const imageScores = images.map(image => {
            let matchCount = 0;
            
            // Count matching tags
            Object.entries(selectedTags).forEach(([category, selectedTag]) => {
                const imageTag = image.tags[category];
                
                // Handle both string and array tags in images
                if (Array.isArray(imageTag)) {
                    if (imageTag.includes(selectedTag)) matchCount++;
                } else if (imageTag === selectedTag) {
                    matchCount++;
                }
            });

            return {
                url: image.url,
                score: matchCount
            };
        });

        // Find highest score
        const maxScore = Math.max(...imageScores.map(img => img.score));
        
        // Get all images with highest score
        const bestMatches = imageScores.filter(img => img.score === maxScore);
        
        // Select random image from best matches
        const selectedImage = bestMatches[Math.floor(Math.random() * bestMatches.length)];
        
        console.log(`[Image Selection] Selected image with ${maxScore} matching tags:`, selectedImage);

        // Set url and generate base64
        window.CurrentImage = selectedImage.url;
        await generateImageData();
        
    } catch (error) {
        console.error("[Context image selection] Error:", error);
    } finally {
        updateWindow({changing:false});
    }
};

async function fetchGithubImage(imageURL) {
    console.log("[Fetching github image] - URL:", imageURL);
    if (imageURL.includes('github.com')) {
        try {
            const response = await fetch(imageURL, {
                headers: {
                    'Authorization': `token ${repoToken}`,
                    'Accept': 'application/vnd.github.v3.raw'
                }
            });
            if (!response.ok) throw new Error('Failed to fetch image from GitHub');
            
            // Convert blob to base64
            const blob = await response.blob();
            const data = new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });
            
            window.CurrentImage = data;
            return data;
        } catch (error) {
            console.error("[Github fetching] Error:", error);
            return imageURL;
        }
    }
    return imageURL;
}

// convert image in base64
async function generateImageData() {
    const currentStage = stages[window.currentStageIndex];
    const fetchURL = window.CurrentImage || currentStage.image;
    console.log("[Generating Image Data] - URL:", fetchURL);

    if (fetchURL && fetchURL.includes('github.com')) {
        // Set loading state
        updateWindow({changing: true, loading: true})
        
        try {
            // Fetch the image only once
            const imageDataUrl = await fetchGithubImage(fetchURL);
            if (window.dynamicImage === 'only-here' || window.dynamicImage === 'both') {
                window.CurrentImage = imageDataUrl;
                oc.thread.customData.CurrentImage = imageDataUrl;
            } else {
                window.CurrentImage = oc.thread.customData.CurrentImage;
            }
            oc.thread.customData.ChatImage = imageDataUrl;
        } catch (error) {
            console.error("[Window Update] Error fetching image:", error);
        } finally {
            window.customImageLoading = false;
            window.customImageChanging = false;
        }
    }
}

/* ----------------------------------- LLM ---------------------------------- */

// Function to validate and normalize JSON response
function validateResponse(response) {
    try {
        // Extract JSON from response (in case there's additional text)
        const jsonMatch = response.match(/\{[\s\S]*\}/);
        if (!jsonMatch) throw new Error("No JSON found in response");
        
        const json = JSON.parse(jsonMatch[0]);
        
        // Validate structure and types
        if (typeof json.stageProgress !== 'number' || 
            typeof json.innerThought !== 'string' ||
            !json.innerThought.trim()) {
            throw new Error("Invalid JSON structure");
        }
        
        // Normalize response
        return {
            stageProgress: Math.max(window.currentStageIndex, Math.min(json.stageProgress, stages.length - 1)),
            innerThought: json.innerThought.trim()
        };
    } catch (error) {
        console.error("Error processing LLM response:", error);
        // Fallback response
        return {
            stageProgress: window.currentStageIndex,
            innerThought: `I need to focus on ${stages[window.currentStageIndex].checkpoint} to progress further...`
        };
    }
}

/**
 * Generates a chat completion using the specified system and user instructions.
 *
 * @param {Object} options - Configuration options for the chat completion
 * @param {string} options.systemInstruction - System-level instruction for context setting
 * @param {string} options.userInstruction - User-level instruction or prompt
 * @param {number} [options.contextMessages=0] - Number of previous messages to include as context
 * @param {Array} [options.additionalMessages=[]] - Optional array of additional messages
 * @param {number} [options.timeout=30] - Timeout for the API call in seconds
 * @returns {Promise<string>} Resolved chat completion response or fallback message
 */
async function generateChatCompletion({
    systemInstruction,
    userInstruction,
    contextMessages = 0,
    allMessages = false,
    additionalMessages = [],
    timeout = 30
}) {
    // Prepare message array with required messages
    const messages = [
        { author: "system", content: systemInstruction },
        { author: "user", content: userInstruction }
    ];

    // Retrieve and format previous context messages if requested
    if (contextMessages > 0) {
        const previousMessages = allMessages 
            ? oc.thread.messages.slice(-contextMessages)
            : oc.thread.messages
                .filter(m => m.author === "ai" || m.author === "user")
                .slice(-contextMessages);
    
        // Create formatted Content
        const formattedContent = 
            `Here are the last ${previousMessages.length} messages for context:\n` +
            previousMessages.map(m => 
                `- [${m.author === "ai" ? oc.character.name : 
                     m.author === "user" ? oc.userCharacter.name : 
                     m.author}]: ${m.content.replace(/\n/g, '\\n')}`
            ).join('\n');
        
        // Insert it as just one message.
        messages.splice(1, 0, {
            author: "system",
            content: formattedContent
        });
    }

    // Add any additional messages
    messages.push(...additionalMessages);

    try {
        // Log the initiation of the chat completion request
        console.log("[LLM - Request] Initiating chat completion", {
            systemInstructionLength: systemInstruction.length,
            userInstructionLength: userInstruction.length,
            contextMessagesCount: contextMessages
        });

        // Set a timeout to prevent indefinite waiting
        const responsePromise = oc.getChatCompletion({ messages });
        const response = await Promise.race([
            responsePromise,
            new Promise((_, reject) =>
                setTimeout(() => reject(new Error("Request timed out")), timeout*1000)
            )
        ]);

        // Check for empty or invalid response
        if (!response || response.trim().length === 0) {
            console.warn("[LLM - Response] Received empty response. Returning fallback message.");
            return "No meaningful response generated.";
        }

        // Log successful response
        console.log("[LLM - Response] Successful completion received", {
            responseLength: response.length
        });

        return response;
    } catch (error) {
        // Comprehensive error handling
        console.error("[LLM - Error] Chat completion failed", {
            errorName: error.name,
            errorMessage: error.message
        });

        // Return a fallback message
        return "Unable to generate response due to an error.";
    }
}