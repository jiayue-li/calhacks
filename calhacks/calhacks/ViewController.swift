//
//  ViewController.swift
//  moosic
//
//  Created by Sera Yang on 10/7/17.
//  Copyright © 2017 com.calhacks. All rights reserved.
//

import UIKit

struct Constants{
    struct Picture {
        static let picFolder: String = "pictures"
    }
}

class ViewController: UIViewController, UINavigationControllerDelegate, UIImagePickerControllerDelegate  {
    
    @IBOutlet weak var imageView: UIImageView!
    var imageName: String?
    var spotify: String?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        print(imageName!)
        print(spotify!)
        imageView.image = UIImage(named: imageName!)
        // Do any additional setup after loading the view, typically from a nib.
    }
    
    @IBAction func generateSong(_ sender: Any) {
        UIApplication.shared.openURL(NSURL(string:spotify!)! as URL)
    }
    //    func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
//        dismiss(animated: false, completion: nil)
//    }
//    
//    func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [String : Any]) {
//        
//        let selectedImage = info[UIImagePickerControllerOriginalImage] as! UIImage
//        imageView.image = selectedImage
//        
//        print("***********")
//        print(selectedImage.accessibilityIdentifier)
//        
//        dismiss(animated: false, completion: nil)
//    }
//    
//    
//    @IBAction func selectPictures(_ sender: Any) {
//        let controller = UIImagePickerController()
//        controller.delegate = self
//        controller.sourceType = .photoLibrary
//        present(controller, animated: false, completion: nil)
//    }
}
