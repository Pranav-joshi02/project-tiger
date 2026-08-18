export type Role="ADMIN"|"FOREST_OFFICER"|"RESEARCHER"|"REVIEWER"|"VIEWER";
export const canReview=(role:Role)=>["ADMIN","FOREST_OFFICER","RESEARCHER","REVIEWER"].includes(role);
