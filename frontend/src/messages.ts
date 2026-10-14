// every message the user can see, worded exactly as in the A3 error table (ER1-ER9)
export const MESSAGES = {
  noMatch: 'No matching station found.', // ER1
  chooseFromList: 'Please choose a station from the list', // ER2
  sameStation: 'Source and destination must be different.', // ER3
  selectBoth: 'Select both stations.', // ER4
  noRoute: 'No route available between the selected stations.', // ER5
  routeFailed: 'Could not compute the route. Please try again.', // ER6
  unexpected: 'Something went wrong.', // ER7
  networkFailed: 'Map data could not be loaded.', // ER8
  drawIncomplete: 'Route could not be fully drawn on the map.', // ER9
} as const
