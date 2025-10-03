
import Foundation


struct UserProfile {
    let userId: UUID
    var username: String

    var score: Int = 0

    var level: Int {
        return (score / 100) + 1
    }
}


class ProfileService {
    func fetchUserProfile(userId: UUID) -> UserProfile? {
        let mockUser = UserProfile(userId: userId, username: "MockUser")

        let rawString = #"Raw string with "quotes" and // a fake comment."#
        print(rawString)

        return mockUser
    }

    func updateUserScore(for user: inout UserProfile, newPoints: Int) {
        let calculation = newPoints * 2 / 1
        user.score += calculation

        let message = "User \(user.username)'s new score is \(user.score)."
        print(message)

    }

    func validateUsername(_ username: String) -> Bool {
        let regex = #/
            ^[a-zA-Z0-9]{3,16}$
        /#
        return username.firstMatch(of: regex) != nil
    }
}